# -*- coding: utf-8 -*-
from __future__ import with_statement
import os
import sys

from fabric import api as fab
from fabric.contrib import files as fab_files
from fabric.contrib.files import exists

from fab_deploy.utils import run_as

from ..base import _, Daemon
from ..deployment import command
from ..utils import upload_template, upload_first


class SuperVisorD(Daemon):

    config_dir = '/etc/supervisor/'

    namespace = 'supervisord'

    def __init__(self, daemon_name=None):
        if daemon_name is None:
            daemon_name = 'supervisord'
        super(SuperVisorD, self).__init__(daemon_name)

    @run_as('root')
    def install_development_libraries(self):
        fab.env.os.install_package('supervisor')

    @command
    @run_as('root')
    def configure(self):
        upload_template(_('supervisor/supervisord.conf'),
                        '/etc/supervisor/supervisord.conf',
                        fab.env,
                        use_jinja=True)


class SuperVisor(object):

    use_gunicorn = False
    use_celery = False
    use_sphinxsearch = False

    namespace = 'supervisor'

    def __init__(self):
        self.listeners = []
        fab.env.supervisord = SuperVisorD()

    def dirs(self):
        return ['etc/supervisor']

    def watch(self, item):
        item.supervisor = True
        if hasattr(item, 'start'):  # XXX
            item.start = item.supervisor_start
        self.listeners.append(item)

    @command
    def install(self):
        for item in self.listeners:
            item.configure()  # reconfigure with supervisor=True
            item.supervisor_configure()

    @command
    def configure(self, install=False):
        if install:
            self.install()
        else:
            self.update()

    @run_as('root')
    def install_development_libraries(self):
        fab.env.supervisord.install_development_libraries()

    def update(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass

    def restart(self):
        pass

    def reload(self):
        pass
