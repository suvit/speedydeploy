# -*- coding: utf-8 -*-
from __future__ import with_statement
import os
import sys

from fabric import api as fab
from fabric.contrib import files as fab_files
from fabric.contrib.files import exists

from fab_deploy.crontab import crontab_set, crontab_add, crontab_show,\
    crontab_remove, crontab_update
from fab_deploy.system import ssh_add_key
from fab_deploy.utils import run_as

from ..base import _, Daemon, Ubuntu
from ..deployment import command
from ..utils import upload_template, upload_first

from celery import RabbitMQ, Celery
from sphinxsearch import *
from supervisor import SuperVisorD, SuperVisor
from cron import CronTab


class DNSManager(object):
    # class for easy create subdomains
    def add_zone(self, zone):
        raise NotImplementedError

    def add_a_record(self, name):
        raise NotImplementedError

    def add_cname_record(self, name):
        raise NotImplementedError


class Memcache(Daemon):

    pid_file = '/var/run/memcached.pid'

    namespace = 'memcache'

    def __init__(self, daemon_name=None):
        if daemon_name is None:
            daemon_name = 'memcached'
        super(Memcache, self).__init__(daemon_name)

    @run_as('root')
    def put_config(self):

        upload_template('memcached/memcached.conf',
                        "/etc/memcached.conf",
                        use_jinja=True)

        upload_template('memcached/memcached',
                        "/etc/init.d/memcached",
                        mode=0755,
                        use_jinja=True)

        fab.run('touch %s' % self.pid_file)
        fab.run('chown nobody %s' % self.pid_file)

    @run_as('root')
    def install(self):

        with fab.settings(warn_only=True):
            self.stop()

        self.put_config()

        self.restart()

    def update(self):
        self.put_config()
        self.restart()

    @run_as('root')
    def install_development_libraries(self):
        fab.env.os.install_package('memcached')

    def install_requirements(self):
        with fab.cd(_('%(remote_dir)s/')):
            fab.run('env/bin/pip install -U python-memcached')

    @command
    def configure(self, install=True):
        memcache = fab.env.memcache
        if install:
            memcache.install()
        else:
            memcache.update()


class PyLibMC(Memcache):
    @run_as('root')
    def install_development_libraries(self):
        super(PyLibMC, self).install_development_libraries()
        os = fab.env.os
        if isinstance(os, Ubuntu) and os.version.split('.') == ['10','4']:
            # XXX default libmemcached-dev in Ubuntu lucid
            # is version 0.31. its too small for pylibmc
            # TODO do not use add-apt-repository, use deb src file
            # https://launchpad.net/~muffinresearch/+archive/pylibmc-build-deps
            os.install_package('python-software-properties')
            fab.run('add-apt-repository ppa:muffinresearch/pylibmc-build-deps')
            fab.run('apt-get update')
        os.install_package('libmemcached-dev')

    def install_requirements(self):
        with fab.cd(_('%(remote_dir)s/')):
            fab.run('env/bin/pip install -U pylibmc')
            fab.run('env/bin/pip install -e git://github.com/jbalogh/django-pylibmc.git#egg=django-pylibmc')


class LogRotate(object):

    config_dir = '/etc/logrotate.d'

    def add_script(self, file_name):
        fab.put(file_name,
                fab.env.os.path.join(self.config_dir,
                                     _('%(user)s')),
                use_sudo=True)


class Scrapy(object):
    def dirs(self):
        return ['data/scrapy']

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
                'log', 'media', 'run',
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
            dirs.extend(self.scrapy.dirs())

        os = fab.env.os
        for directory in dirs:
            os.mkdir(os.path.join(_('%(remote_dir)s'), directory))

    @command(same_name=True, aliases=('update_virtual_env',))
    def install_requirements(self):
        if self.use_server:
            fab.env.server.install_requirements()

        if self.use_memcache:
            fab.env.memcache.install_requirements()

        with fab.cd(_('%(remote_dir)s')):
            if exists(_("%(project_name)s/requirements.txt")):
                fab.run(_("env/bin/pip install -r %(project_name)s/requirements.txt"))

        if self.use_django:
            self.django.install_requirements()

    @command(same_name=True)
    def update_reqs(self):
        with fab.cd(_('%(remote_dir)s/')):
            if exists(_("%(project_name)s/requirements.txt")):
                fab.run(_("env/bin/pip install -U -r"
                          " %(project_name)s/requirements.txt"))

    @run_as('root')
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
            os.install_package('libjpeg62 libjpeg62-dev')
            os.install_package('libfreetype6 libfreetype6-dev')

        for name in ('os', 'server', 'db', 'supervisor',
                     'scrapy', 'vcs', 'celery', 'sphinxsearch',
                     'memcache'):
            if getattr(self, 'use_' + name, False):
                getattr(fab.env, name).install_development_libraries()

    @run_as('root')
    @command(same_name=True)
    def install_setuptools(self):
        os = fab.env.os.install_package("python-setuptools build-essential")

        fab.sudo("easy_install distribute")
        fab.sudo("easy_install pip")

    @run_as('root')
    @command(same_name=True)
    def install_virtualenv(self):
        fab.sudo("easy_install virtualenv")

    @command(same_name=True)
    def create_env(self):
        with fab.cd(_('%(remote_dir)s')):
            fab.run("virtualenv env")

    def backup(self):
        with fab.cd(_('%(remote_dir)s')):
            fab.env.os.mkdir(_("backup/%(backup_dirname)s"))
            fab.run(_("tar -czf %(project_name)s_%(backup_dirname)s.tgz"
                      " backup/%(backup_dirname)s/%(project_name)s"))
