from fabric import api as fab

from ..base import Debian
from ..deployment import _
from ..project import LogRotate
from ..project.cron import CronTab, BCronTab
from ..database import Maria52Database

from .base import Provider


class NetangelsShared(Provider):

    shared = True

    def __init__(self):
        super(NetangelsShared, self).__init__()

        fab.env.os = Debian()

        fab.env.remote_dir = _("/home/%(user)s/%(instance_name)s/")

        fab.env.cron = BCronTab()


class Lite(NetangelsShared):
    pass


class Standard(NetangelsShared):
    pass


class Professional(NetangelsShared):
    pass


class NetangelsVDS(Provider):
    def __init__(self):
        super(NetangelsVDS, self).__init__()

        fab.env.os = Debian()

        fab.env.remote_dir = _("/home/%(user)s/")

        fab.env.db = Maria52Database()

        fab.env.cron = CronTab()
        fab.env.logrotate = LogRotate()


class VDS512(NetangelsVDS):
    pass
VDS2 = VDS512
