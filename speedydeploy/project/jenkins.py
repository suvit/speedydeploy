# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta

from fabric import api as fab, colors
from fabric.contrib.files import exists

from fab_deploy.utils import run_as

from ..base import _, Daemon, ObjectWithCommands
from ..deployment import command
from ..utils import upload_first


class Jenkins(ObjectWithCommands):

    namespace = 'jenkins'

    update_status_file = '.reqs_updated'
    test_repo = 'git+ssh://git@bitbucket.org/suvitorg/django-pwutils#egg=pwutils[tests]'

    def __init__(self, settings='pwutils.settings.jenkins'):
        self.settings = settings
        fab.env.setdefault('expire_timedelta', timedelta(days=1))

    def local_exist(self, path, directory=False):
        operator = '-d' if directory else '-f'
        with fab.settings(warn_only=True):
            res = fab.local('test %s %s' % (operator, path), capture=True)
            return int(res.return_code) == 0

    def install_test_reqs(self):
        fab.local('env/bin/pip install'
                  ' -U %s' % self.test_repo)

    def install_project_reqs(self, future=False):
        fab.local('env/bin/pip install -U -r requirements.txt')

        if future:
            self.install_future_reqs()

    @command
    def install_reqs(self):
        self.install_test_reqs()
        self.install_project_reqs()

    def install_future_reqs(self):
        if self.local_exist('requirements/future.txt'):
            fab.local('env/bin/pip install -U -r requirements/future.txt')

    def set_update_time(self):
        fab.local('echo %s > %s' % (time.time(),
                                    self.update_status_file))

    def need_update(self):
        try:
            with fab.settings(warn_only=True):
                update_ts = float(fab.local('cat %s' % self.update_status_file,
                                            capture=True).strip())
        except ValueError:
            update_ts = 0

        last_update = datetime.fromtimestamp(update_ts)

        if (datetime.now() - last_update) > fab.env['expire_timedelta']:
            print colors.red('update requirements needed')
            return True
        else:
            print colors.white('update requirements not needed')
            return False

    @command
    def test_project(self, future=False):
        if not self.local_exist('env', directory=True):
            fab.local('virtualenv env --system-site-packages')

        fab.local("find . -name '*.pyc' -delete")

        if self.need_update():
            self.install_test_reqs()
            self.install_project_reqs(future=future)
            self.set_update_time()

        fab.local('env/bin/python manage.py jenkins'
                  ' --settings=%s' % self.settings)

class JenkinsServer(Daemon):

    namespace = 'jenkinsd'

    home_dir = '/var/lib/jenkins/'

    def __init__(self, **kwargs):
        kwargs.setdefault('daemon_name', 'jenkins')
        super(JenkinsServer, self).__init__(**kwargs)

    @command
    def install(self):
        # getted from http://habrahabr.ru/blogs/django/132521/
        # XXX for Debian only

        fab.sudo('wget -q -O - http://pkg.jenkins-ci.org/debian/jenkins-ci.org.key | sudo apt-key add -')
        fab.sudo('echo "deb http://pkg.jenkins-ci.org/debian binary/"'
                ' > /etc/apt/sources.list.d/jenkins.list')

        fab.sudo('apt-get update')
        fab.sudo('apt-get install jenkins')

        self.install_plugins()

    @run_as('jenkins')
    def install_plugins(self):
        with fab.cd(self.home_dir):
            fab.run('wget http://localhost:8080/jnlpJars/jenkins-cli.jar')

            jenkins_cli = ('java -jar jenkins-cli.jar'
                           ' -s http://localhost:8080/')
            for plugin in ['Cobertura',
                           'Violations',
                           'Git',
                           'Green ball']:
               fab.run('%s install-plugin %s' % (jenkins_cli, plugin))

            fab.run('%s safe-restart' % jenkins_cli)

    def configure_webserver(self):
        server = fab.env.server
        server.configure(template=[_('nginx/%(domain)s.conf'),
                                   'jenkins/%s.conf' % server.name])

    @command
    def configure(self):
        self.configure_webserver()
