from .config import config
from .host import Host

class Yardc(object):
    def __init__(self):
        self.config = config

    @property
    def hosts(self):
        if not hasattr(self, '_hosts'):
            self._hosts = dict()
            for host in config['hosts']:
                if host['name'] in self._hosts:
                    raise ValueError("Duplicated host alias")
                self._hosts[host['name']] = Host(host['uri'], host['name'])
        return self._hosts
