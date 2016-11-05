import io
import re
import time
import gpgme
import base64
import fnmatch
import libvirt
import logging
import subprocess
import defusedxml.ElementTree as ET
from .ssh import Forwarder
from .config import config

VM_STATE = {
        0: 'NOSTATE',
        1: 'RUNNING',
        2: 'BLOCKED',
        3: 'PAUSED',
        4: 'SHUTDOWN',
        5: 'SHUTOFF',
        6: 'CRASHED',
        7: 'PMSUSPENDED'
}

RDP_PORT = 3389

class Machine(object):
    def __init__(self, host, name):
        self.host = host
        self.name = name

    @property
    def conn(self):
        return self.host.conn

    @property
    def dom(self):
        if not hasattr(self, '_dom'):
            self._dom = self.conn.lookupByName(self.name)
        return self._dom

    @property
    def description(self):
        return ET.fromstring(self.dom.XMLDesc(0))

    @property
    def ip_address(self):
        if getattr(self, '_ip_address', None) is None:
            self._ip_address = self._get_ip_address()
        return self._ip_address

    def _get_ip_address(self):
        if_addresses = self.dom.interfaceAddresses(0)
        for vlan in if_addresses:
            for address in if_addresses[vlan]['addrs']:
                return address['addr']
        return None

    def wait_ip_address(self):
        logging.info("Waiting an IP address for the domain %s", self.domain_name)
        wait_until = time.time() + 300
        while wait_until > time.time():
            ip_address = self.ip_address
            logging.debug("Wait an IP address: value=%s", ip_address)
            if ip_address is not None:
                return
            time.sleep(5)
        raise RuntimeError("Timeout in waiting ip address of domain %s" % self.domain_name)

    @property
    def status_code(self):
        return self.dom.state()[0]

    @property
    def profile(self):
        matched_mp = None
        profile = None
        for mp in config.get('machine_profiles', []):
            if fnmatch.fnmatchcase(self.host.name, mp["host"]):
                if fnmatch.fnmatchcase(self.name, mp["machine"]):
                    matched_mp = mp["profile"]
                    break
        profile = None
        if matched_mp in config.get("profiles", {}):
            profile = config["profiles"][matched_mp]
            if "encrypted_password" in profile:
                encrypted_password = io.BytesIO(
                    base64.decodebytes(profile["encrypted_password"].encode("utf-8"))
                )
                decrypted_password = io.BytesIO()
                ctx = gpgme.Context()
                ctx.decrypt(encrypted_password, decrypted_password)
                profile['password'] = decrypted_password.getvalue().decode("utf-8")

        return profile
    
    @property
    def status(self):
        return VM_STATE[self.status_code]


    def start(self):
        try:
            self.dom.create()
        except libvirt.libvirtError:
            return False
        return True

    def stop(self):
        try:
            self.dom.shutdown()
        except libvirt.libvirtError:
            return False
        return True

    def get_domain_description(self):
        return ET.fromstring(self.dom.XMLDesc())

    def rdp(self, clipboard=True):
        profile = self.profile
        if profile is None:
            raise ValueError("Unable to get profile")

        if self.host.connection_type == "local":
            rdp_host = self.ip_address
            rdp_port = RDP_PORT
        elif self.host.connection_type == "ssh":
            fw = Forwarder(self.host.hostname, self.host.port, self.host.username, self.ip_address, RDP_PORT)
            fw.forward()
            rdp_host = "localhost"
            rdp_port = fw.listen_port
        else:
            raise ValueError("Unknown connection type")

        cmd = [
            "/usr/bin/xfreerdp",
            "/cert-ignore", # ...
            "/w:%s" % config.get("rdp", dict()).get("width", 1920),
            "/h:%s" % config.get("rdp", dict()).get("height", 1080),
            "/v:%s" % rdp_host,
            "/port:%s" % rdp_port

        ]

        if "username" in profile:
            cmd.append("/u:%s" % profile["username"])
        if "password" in profile:
            cmd.append("/p:%s" % profile["password"])
        
        for share in profile.get("shares", []):
            cmd.append("/drive:%s,%s" % (share['name'], share['path']))
        if clipboard:
            cmd.append("+clipboard")
        
        subprocess.run(cmd)
