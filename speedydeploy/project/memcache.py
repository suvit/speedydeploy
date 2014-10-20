# -*- coding: utf-8 -*-
from __future__ import with_statement
import os
import sys

from fabric import api as fab
from fabric.contrib import files as fab_files
from fabric.contrib.files import exists

from fab_deploy.system import ssh_add_key
from fab_deploy.utils import run_as

from ..base import _, Daemon, Ubuntu
from ..deployment import command
from ..utils import upload_template, upload_first


# TODO rename to Memcached
# and add project depends Memcache
class Memcache(Daemon):

    pid_file = '/var/run/memcached.pid'

    namespace = 'memcache'

    def __init__(self, daemon_name=None):
        if daemon_name is None:
            daemon_name = 'memcached'
        super(Memcache, self).__init__(daemon_name)

    def dirs(self):
        return ["etc/memcache/",
               ]

    def put_config(self):

        upload_template('memcached/memcached.conf',
                        _("%(remote_dir)s/etc/memcached.conf"),
                        use_jinja=True)

        #upload_template('memcached/memcached',
        #                "/etc/init.d/memcached",
        #                mode=0755,
        #                use_sudo=True,
        #                use_jinja=True)

        fab.sudo('touch %s' % self.pid_file)
        fab.sudo('chown nobody %s' % self.pid_file)

    def install(self):

        with fab.settings(warn_only=True):
            self.stop()

        self.put_config()

        self.restart()

    def update(self):
        self.put_config()
        self.restart()

    def install_development_libraries(self):
        fab.env.os.install_package('memcached')

    def install_requirements(self):
        with fab.cd(_('%(remote_dir)s/')):
            fab.run('%(virtualenv)s/bin/pip install -U python-memcached')

    @command
    def configure(self, install=False):
        memcache = fab.env.memcache
        if install:
            memcache.install()
        else:
            memcache.update()


class PyLibMC(Memcache):
    def install_development_libraries(self):
        os = fab.env.os
        if isinstance(os, Ubuntu) and os.version.split('.') == ['10','4']:
            # XXX default libmemcached-dev in Ubuntu lucid
            # is version 0.31. its too small for pylibmc
            os.install_package('python-software-properties')
            fab.sudo('add-apt-repository ppa:muffinresearch/pylibmc-build-deps')
            fab.sudo('apt-get update')

        super(PyLibMC, self).install_development_libraries()
        os.install_package('libmemcached-dev')

    def install_requirements(self):
        with fab.cd(_('%(remote_dir)s/')):
            fab.run('env/bin/pip install -U pylibmc')
            fab.run('env/bin/pip install -U django-pylibmc')
