from fabric import api as fab

from ..base import Gentoo
from ..deployment import _
from ..webserver import FcgiWrapper
from ..project.cron import CronTab

from .base import Provider


class OnegbShared(Provider):

    shared = True

    def __init__(self):
        super(OnegbShared, self).__init__()

        fab.env.os = Gentoo()

        fab.env.home_dir = _("/home/virtwww/%(user)s/")
        fab.env.remote_dir = _("%(home_dir)s%(project_name)s")

        domain = _('%(project_name)s.ru')  # XXX TODO
        fab.env.server = FcgiWrapper(domain=domain)
        fab.env.apache_fcgi_full = True
        fab.env.worker_count = 3

        fab.env.cron = CronTab()
