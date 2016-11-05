import re
import libvirt
import defusedxml.ElementTree as ET
from .machine import Machine

class Host(object):
    connection_type = None
    def __init__(self, uri, name):
        self.uri = uri
        self.name = name
        self._parse_uri()

    def _parse_uri(self):
        if self.uri == "qemu:///system":
            self.connection_type = "local"
            return
        res = re.search("qemu\\+ssh://([^@]*)@([^/]+)/system", self.uri)
        if res is not None:
            self.username, self.hostname = res.groups()
            host_splitted = self.hostname.split(':')
            if len(host_splitted) == 1:
                self.port = 22
            elif len(host_splitted) == 2:
                self.hostname = host_splitted[0]
                self.port = host_splitted[1]
            else:
                raise ValueError("Unable to parse host in uri")
            self.connection_type = "ssh"
            return
    @property
    def conn(self):
        if not hasattr(self, '_conn'):
            self._conn = libvirt.open(self.uri)
        return self._conn

    @property
    def machines(self):
        machines = dict()
        for machine in self.conn.listAllDomains():
            machines[machine.name()] = Machine(self, machine.name())
        return machines
