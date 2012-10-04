from fabric import api as fab

from ..base import Debian

from .base import Provider

class NetangelsShared(Provider):

    shared = True

    def __init__(self):
        super(NetangelsShared, self).__init__()

        fab.env.os = Debian()


class Lite(NetangelsShared):
    pass


class NetangelsVDS(Provider):
    pass


class VDS512(NetangelsVDS):
    pass
