from fabric import api as fab

from ..base import FreeBSD
from ..deployment import _
from ..project.cron import CronTab
from ..database import Maria52Database

from .base import Provider


class BeelineShared(Provider):

    shared = True

    def __init__(self):
        super(BeelineShared, self).__init__()

        fab.env.os = FreeBSD()
        fab.env.shell = '/usr/bin/bash -l -c'

        fab.env.home_dir = _("/web/%(user)s")
        fab.env.remote_dir = _("/web/%(user)s/%(instance_name)s/")

        fab.env.cron = CronTab()
