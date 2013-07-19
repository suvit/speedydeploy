from fabric import api as fab

from ..base import Ubuntu, Ubuntu104
from ..deployment import _
from ..project.cron import CronTab
from ..project import LogRotate

from .base import Provider

class Hetzner(Provider):
    def __init__(self):
        super(Hetzner, self).__init__()

        fab.env.remote_dir = _("/home/%(user)s/")
        fab.env.home_dir = _("/home/%(user)s/")

        fab.env.cron = CronTab()
        fab.env.logrotate = LogRotate()

class VQ7(Hetzner):
    pass


class VQ12(Hetzner):
    pass


class EX4(Hetzner):
    pass


class EX4S(EX4):
    pass


class EX40(EX4):
    pass


class EX40SSD(EX4):
    pass


class EX5(Hetzner):
    pass


class EX6(Hetzner):
    pass


class EX8(Hetzner):
    pass


class EX8S(Hetzner):
    pass
