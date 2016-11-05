import os
import time
import random
import logging
import paramiko
import select
import socket
import threading
try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer

class ForwardServer (SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True
    

class Handler (SocketServer.BaseRequestHandler):

    def handle(self):
        try:
            chan = self.ssh_transport.open_channel('direct-tcpip',
                                                   (self.chain_host, self.chain_port),
                                                   self.request.getpeername())
        except Exception as e:
            print('Incoming request to %s:%d failed: %s' % (self.chain_host,
                                                              self.chain_port,
                                                              repr(e)))
            return
        if chan is None:
            print('Incoming request to %s:%d was rejected by the SSH server.' %
                    (self.chain_host, self.chain_port))
            return

        print('Connected!  Tunnel open %r -> %r -> %r' % (self.request.getpeername(),
                                                            chan.getpeername(), (self.chain_host, self.chain_port)))
        while True:
            r, w, x = select.select([self.request, chan], [], [])
            if self.request in r:
                data = self.request.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                self.request.send(data)
                
        peername = self.request.getpeername()
        chan.close()
        self.request.close()
        print('Tunnel closed from %r' % (peername,))


class Forwarder(object):
    def __init__(self, hostname, port, username, remote_host, remote_port):
        self.hostname = hostname
        self.port = port
        self.username = username
        self.remote_host = remote_host
        self.remote_port = remote_port

    @property
    def listen_port(self):
        if getattr(self, "_listen_port", None) is None:
            self._listen_port = random.randint(4200, 4400)
        return self._listen_port

    @property
    def client(self):
        if getattr(self, '_client', None) is None:
            client = paramiko.SSHClient()
            client.load_host_keys(os.path.expanduser("~/.ssh/known_hosts"))
            client.connect(self.hostname, self.port, self.username)
            self._client = client
        return self._client

    @property
    def forward_server(self):
        if getattr(self, '_forward_server', None) is None:
            # this is a little convoluted, but lets me configure things for the Handler
            # object.  (SocketServer doesn't give Handlers any way to access the outer
            # server normally.)
            class SubHander (Handler):
                chain_host = self.remote_host
                chain_port = self.remote_port
                ssh_transport = self.client.get_transport()
            server = ForwardServer(('127.0.0.1', self.listen_port), SubHander)
            server_thread = threading.Thread(target=server.serve_forever)
            # Exit the server thread when the main thread terminates
            server_thread.daemon = True
            server_thread.start()
            print("Server loop running in thread:", server_thread.name)
            self._forward_server = server 
        return self._forward_server


    def forward(self):
        for i in range(10):
            try:
                return self.forward_server
            except:
                time.sleep(2)
                self._listen_port = None
                logging.exception("Unable start forward server")
        raise Exception("Unable to start forward server")
