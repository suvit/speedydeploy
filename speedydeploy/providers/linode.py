from fabric import api as fab

from ..base import Ubuntu, Ubuntu104
from ..deployment import _
from ..project.cron import CronTab
from ..project import LogRotate

from .base import Provider


class Linode(Provider):
    def __init__(self):
        super(Linode, self).__init__()

        fab.env.os = Ubuntu104()

        fab.env.remote_dir = _("/home/%(user)s/")
        fab.env.home_dir = _("/home/%(user)s/")

        fab.env.cron = CronTab()
        fab.env.logrotate = LogRotate()


class Linode512(Linode): # OLD
    pass


class Linode768(Linode): # OLD
    pass


class Linode1024(Linode): # OLD
    pass


class Linode1(Linode):
    pass


class Linode2(Linode):
    pass
