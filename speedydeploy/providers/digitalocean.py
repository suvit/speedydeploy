from fabric import api as fab

from ..base import Ubuntu, Ubuntu 124, Ubuntu124x64
from ..deployment import _
from ..project.cron import CronTab
from ..project import LogRotate

from .base import Provider


class DigitalOcean(Provider):
    def __init__(self):
        super(DigitalOcean, self).__init__()

        fab.env.os = Ubuntu124x64()

        fab.env.remote_dir = _("/home/%(user)s/")
        fab.env.home_dir = _("/home/%(user)s/")

        fab.env.cron = CronTab()
        fab.env.logrotate = LogRotate()


class Droplet(DigitalOcean):
    pass


class Droplet1(Droplet):
    pass


class Droplet2(Droplet):
    pass
