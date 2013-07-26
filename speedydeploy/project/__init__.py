# -*- coding: utf-8 -*-
from __future__ import with_statement
import os
import sys

from fabric import api as fab
from fabric.contrib import files as fab_files
from fabric.contrib.files import exists

from fab_deploy.system import ssh_add_key
from fab_deploy.utils import run_as

from ..base import _, Daemon, Debian, RedHat, Ubuntu
from ..deployment import command
from ..utils import upload_template, upload_first

from celery import RabbitMQ, Celery
from sphinxsearch import *
from supervisor import SuperVisorD, SuperVisor
from cron import CronTab
from memcache import Memcache, PyLibMC
from jenkins import Jenkins


class DNSManager(object):
    # class for easy create subdomains
    def add_zone(self, zone):
        raise NotImplementedError

    def add_a_record(self, name):
        raise NotImplementedError

    def add_cname_record(self, name):
        raise NotImplementedError


class LogRotate(object):

    namespace = 'logrotate'

    config_dir = '/etc/logrotate.d/'

    def add_script(self, file_name, remote_name=None):

        remote_name = remote_name or _('%(user)s')

        upload_template(file_name,
                        self.config_dir + 'speedydeploy-' + remote_name,
                        fab.env,
                        use_jinja=True,
                        use_sudo=True,
                        backup=False)


class Scrapy(object):

    namespace = 'scrapy'

    def dirs(self):
        return ['data/scrapy']

    @command
    def configure(self):
        upload_first(['scrapy/settings_local.py',
                      'scrapy/settings_default.py'],
                     _('%(remote_dir)s/%(project_name)s/scrapy/'),
                     fab.env,
                     use_jinja=True)

    def install_development_libraries(self):
        fab.env.os.install_package('libxml2 libxml2-dev libxslt-dev')


class Project(object):

    namespace = 'project'

    use_os = property(lambda self: hasattr(fab.env, 'os'))
    use_cron = property(lambda self: hasattr(fab.env, 'cron'))
    use_server = property(lambda self: hasattr(fab.env, 'server'))
    use_db = property(lambda self: hasattr(fab.env, 'db'))
    use_memcache = property(lambda self: hasattr(fab.env, 'memcache'))
    use_celery = property(lambda self: hasattr(fab.env, 'celery'))
    use_sphinxsearch = property(lambda self: hasattr(fab.env, 'sphinxsearch'))
    use_vcs = property(lambda self: hasattr(fab.env, 'vcs'))
    use_logrotate = property(lambda self: hasattr(fab.env, 'logrotate'))

    use_supervisor = property(lambda self: hasattr(fab.env, 'supervisor'))
    use_scrapy = property(lambda self: hasattr(fab.env, 'scrapy'))
    use_django = property(lambda self: hasattr(self, 'django'))

    use_pil = True # project depends
    use_pip = True

    @command
    def install(self):
        dirs = ['', 'backup', 'data', 'etc',
                'media', 'run',
                'tmp', 'utils']

        if self.use_celery:
            dirs.extend(fab.env.celery.dirs())

        if self.use_sphinxsearch:
            dirs.extend(fab.env.sphinxsearch.dirs())

        if self.use_server:
            dirs.extend(fab.env.server.dirs())

        if self.use_supervisor:
            dirs.extend(fab.env.supervisor.dirs())

        if self.use_scrapy:
            dirs.extend(fab.env.scrapy.dirs())

        os = fab.env.os
        for directory in dirs:
            os.mkdir(os.path.join(_('%(remote_dir)s'), directory))

        self.update_log()

    def update_log(self):
        fab.sudo(_('ln -s /var/log/speedydeploy/%(user)s/'
                   ' %(remote_dir)slog'
                  ))

    @command(same_name=True, aliases=('update_virtual_env',))
    def install_requirements(self):
        self.update_reqs(update=False)

    @command(same_name=True)
    def update_reqs(self, update=True):
        self.update_virtualenv()

        if self.use_server:
            fab.env.server.install_requirements()

        if self.use_memcache:
            fab.env.memcache.install_requirements()

        if self.use_django:
            self.django.install_requirements(update=update)

    @command(same_name=True)
    def install_development_libraries(self):
        os = fab.env.os

        if self.use_pip:
            # vcs (needed by pip) XXX remove to pip object
            os.install_package('subversion')
            os.install_package('mercurial')
            os.install_package('git-core')

        if self.use_pil:
            # must have to compile PIL jpeg support
            # XXX remove to PIL object
            if isinstance(os, Debian):
                os.install_package('libjpeg62 libjpeg62-dev')
                os.install_package('libfreetype6 libfreetype6-dev')
            elif isinstance(os, RedHat):
                os.install_package('zlib-devel libjpeg-devel freetype-devel')

        for name in ('os', 'server', 'db', 'supervisor',
                     'scrapy', 'vcs', 'celery', 'sphinxsearch',
                     'memcache'):
            if getattr(self, 'use_' + name, False):
                getattr(fab.env, name).install_development_libraries()

    @command(same_name=True)
    def install_setuptools(self):
        os = fab.env.os.install_package("python-setuptools build-essential")

        fab.sudo("easy_install distribute")
        fab.sudo("easy_install pip")

    @command(same_name=True)
    def install_virtualenv(self):
        fab.sudo("pip install virtualenv")

    @command(same_name=True)
    def update_virtualenv(self):
        with fab.cd(_('%(remote_dir)s/')):
            fab.run('env/bin/pip install -U "pip<1.4"')
            fab.run('env/bin/pip install -U virtualenv')

    @command(same_name=True)
    def create_env(self):
        with fab.cd(_('%(remote_dir)s')):
            fab.run("virtualenv env")

    def backup(self):
        with fab.cd(_('%(remote_dir)s')):
            fab.env.os.mkdir(_("backup/%(backup_dirname)s"))
            fab.run(_("tar -czf %(project_name)s_%(backup_dirname)s.tgz"
                      " backup/%(backup_dirname)s/%(project_name)s"))

    @command
    def configure(self):
        if fab.env.logrotate:
            fab.env.logrotate.add_script('project/logrotate')
