from fabric import api as fab

from ..base import Ubuntu
from ..deployment import _

from .base import Provider


class Linode(Provider):
    def __init__(self):
        super(Linode, self).__init__()

        fab.env.os = Ubuntu()

        fab.env.remote_dir = _("/home/%(user)s")

        fab.env.cron = CronTab()


class Linode512(Linode):
    pass


class Linode768(Linode):
    pass


class Linode1024(Linode):
    pass
