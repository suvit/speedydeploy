# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta

from fabric import api as fab, colors
from fabric.contrib.files import exists


class Jenkins(object):

    update_status_file = '.reqs_updated'
    test_repo = 'git+ssh://git@bitbucket.org/suvitorg/django-pwutils#egg=pwutils[tests]'

    def __init__(self, settings='settings_jenkins'):
        self.settings = settings
        fab.env.setdefault('expire_timedelta', timedelta(days=1))

    def local_exist(self, path, directory=False):
        operator = '-d' if directory else '-f'
        with fab.settings(warn_only=True):
            res = fab.local('test %s %s' % (operator, path), capture=True)
            print int(res.return_code) == 0
            return int(res.return_code) == 0

    def install_test_reqs(self):
        fab.local('env/bin/pip install'
                  ' %s' % self.test_repo)

    def install_project_reqs(self, future=False):
        fab.local('env/bin/pip install -U -r requirements.txt')

        if future:
            self.install_future_reqs()

    def install_future_reqs(self):
        if self.local_exist('requirements/future.txt'):
            fab.local('env/bin/pip install -U -r requirements/future.txt')

    def need_update(self):
        try:
            with fab.settings(warn_only=True):
                update_ts = float(fab.local('cat %s' % self.update_status_file,
                                            capture=True).strip())
        except ValueError:
            update_ts = 0

        last_update = datetime.fromtimestamp(update_ts)

        now = datetime.now()

        if (now - last_update) > fab.env['expire_timedelta']:
            fab.local('echo %s > %s' % (time.time(),
                                          self.update_status_file))
            print colors.red('update requirements needed')
            return True
        else:
            print colors.white('update requirements not needed')
            return False

    def test_project(self, future=False):
        if not self.local_exist('env', directory=True):
            fab.local('virtualenv env --system-site-packages')

        if self.need_update():
            self.install_test_reqs()
            self.install_project_reqs(future=future)

        fab.local('env/bin/python manage.py jenkins'
                  ' --settings=%s' % self.settings)
