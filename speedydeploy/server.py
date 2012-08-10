# -*- coding: utf-8 -*-
from __future__ import with_statement
import os
import time

from fabric import api as fab

from fab_deploy.utils import run_as

from base import _, Daemon
from utils import upload_template, upload_first


class Server(Daemon):

    config_dir = None

    def __init__(self, name, domain):
        super(Server, self).__init__(name)

        self.env = fab.env
        self.env['domain'] = domain

    def enable_site(self, name):
        server_dir = self.config_dir
        fab.sudo("ln -s %(server_dir)ssites-available/%(name)s"
                 " %(server_dir)ssites-enabled/%(name)s" % locals() )

    def disable_site(self, name):
        server_dir = self.config_dir
        fab.sudo("rm -f %(server_dir)ssites-enabled/%(name)s" % locals() )

    def remove_site(self, name):
        self.disable_site(name)
        server_dir = self.config_dir
        fab.sudo("rm -f %(server_dir)ssites-available/%(name)s" % locals() )

    def install_development_libraries(self):
        pass

    def install_requirements(self):
        pass

    def dirs(self):
        return []


class Backend(object): #TODO inherit Server
    name = NotImplemented


class FcgiBackend(Backend):
    name = 'fcgi'


class Gunicorn(Backend):
    name = 'gunicorn'


class WsgiBackend(Backend):
    name = 'wsgi'


class UwsgiBackend(Backend):
    name = 'uwsgi'


class ServerWithBackend(Server):
    backend = NotImplemented


class ApacheServer(Server):
    local_dir = 'apache'

    def __init__(self, **kwargs):
        kwargs.setdefault('name', 'apache')
        super(ApacheServer, self).__init__(**kwargs)


class Apache2Server(ApacheServer):

    config_dir = '/etc/apache2/'

    def __init__(self, **kwargs):
        kwargs.setdefault('name', 'apache2')
        super(ApacheServer, self).__init__(**kwargs)

    @run_as('root')
    def configure(self):
        upload_template(_('apache/%(domain)s.conf'),
                        fab.env.os.path.join(self.config_dir, _('sites-available/%(domain)s.conf') ),
                        fab.env,
                        use_sudo=True,
                        use_jinja=True)

    @run_as('root')
    def restart(self):
        fab.sudo("apache2ctl -k graceful")

    def status(self):
        fab.sudo("apache2ctl status")

    @run_as('root')
    def enable_site(self, name):
        fab.sudo("a2ensite %s" % name)

    @run_as('root')
    def disable_site(self, name):
        fab.sudo("a2dissite %s" % name)

    def install_development_libraries(self):
        os = fab.env.os
        os.install_package('apache2')


class NginxServer(Server):

    config_dir = '/etc/nginx/'
    log_dir = '/var/log/nginx/'

    def __init__(self, **kwargs):
        kwargs.setdefault('name', 'nginx')
        super(NginxServer, self).__init__(**kwargs)

    def stop(self, pty=True):
        super(NginxServer, self).stop(pty=pty)
        self.stop_backend()

    def start(self, pty=True):
        super(NginxServer, self).start(pty=pty)
        self.start_backend()

    def stop_backend(self):
        pass

    def start_backend(self):
        pass

    def reload(self):
        self.stop_backend()
        time.sleep(2)
        self.start_backend()

    def install_development_libraries(self):
        os = fab.env.os
        os.install_package('nginx')

    def update_static_files(self):
        remote_dir = fab.env['remote_dir']
        files = fab.env['server_static_files'] = list()

        test_dirs = ['nginx/files',
                     _('nginx/%(domain)s')]

        for dir in test_dirs:

            if not os.path.exists(dir):
                continue

            for filename in os.listdir(dir):
                if filename.startswith('.'):
                    continue
                # TODO use jinia template engine to render txt files(robots.txt)
                fab.put("%s/%s" % (dir, filename),
                        "%s/media/%s" % (remote_dir, filename))
                files.append(filename)

    @run_as('root')
    def configure(self):

        self.update_static_files() #added static_files var for fab.env

        upload_first([_('nginx/%(domain)s.conf'),
                      'nginx/default.conf'],
                     fab.env.os.path.join(self.config_dir, _('sites-available/%(domain)s.conf') ),
                     fab.env,
                     use_sudo=True,
                     use_jinja=True)

        os = fab.env.os
        os.mkdir(os.path.join(self.log_dir, _('%(user)s')))

        self.disable_site('%(domain)s.conf' % self.env)
        self.enable_site('%(domain)s.conf' % self.env)


class Apache2ServerWithFcgi(Apache2Server):

    backend = FcgiBackend()

    def local_path(self, path=''):
        return os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            self.local_dir,
                                            path)
                              )

    def configure(self):
        self.put_site_config(self.domain)
        self.put_fcgi_scripts()

    def put_site_config(self, site=None):
        if site is None:
            site = fab.env.domain

        context = dict(project=fab.env.user,
                       project_name=fab.env.project_name,
                       domain=site,
                       domain_escaped=site.replace('.','\.'))

        upload_template('apache/.htaccess',
                        '/home/%s/%s/www/.htaccess' % (fab.env.user, site),
                        context,
                        use_jinja=True)

    def put_fcgi_scripts(self):
        context = dict(project=fab.env.user,
                       project_name=fab.env.project_name,
                       domain='%s.ru' % fab.env.user,
                       domain_escaped='%s\\.ru' % fab.env.user)

        upload_template("apache/project-sh.fcgi",
                        '/var/www/%(project)s/%(project)s-sh.fcgi' % context,
                        context=context,
                        mode=0755,
                        use_jinja=True)

        upload_template("apache/project.fcgi",
                        '/var/www/%(project)s/%(project)s.fcgi' % context,
                        context=context,
                        mode=0755,
                        use_jinja=True)


class Apache2ServerWithWsgi(Apache2Server):

    backend = WsgiBackend()

    # Try to copy from Deployment class
    def configure(self):
        fab.put(self.local_dir + _("/%(instance_name)s"), "/tmp/")
        fab.sudo(_("cp /tmp/%(instance_name)s /etc/apache2/sites-available/%(instance_name)s"))
        self.enable_site(_("%(instance_name)s"))

        fab.put(self.local_dir + "/django.wsgi", "/tmp/")
        fab.sudo("chmod 755 /tmp/django.wsgi")
        fab.sudo(_("mkdir -p %(remote_dir)s/%(project_name)s/etc/apache"))
        fab.sudo(_("cp /tmp/django.wsgi %(remote_dir)s/%(project_name)s/etc/apache/django.wsgi"))
        fab.sudo(_("chown %(user)s:www-data -R %(remote_dir)s/%(project_name)s"))
        fab.sudo(_("chmod u=rwx,g=rx,o= -R %(remote_dir)s/%(project_name)s"))
        self.restart()


class NginxFcgi(NginxServer):

    backend = FcgiBackend()

    def __init__(self, **kwargs):
        super(NginxServerWithFcgi, self).__init__(**kwargs)

    def install_requirements(self):
        with fab.cd(_('%(remote_dir)s/')):
            fab.run('env/bin/pip install -U flup')

    def stop_backend(self):
        with fab.settings(warn_only=True):
            fab.run("cat %(remote_dir)s/run/%(domain)s.pid | xargs kill -TERM" % self.env)

    def start_backend(self):
        with fab.cd('%(remote_dir)s/%(project_name)s' % self.env):
            fab.run('../env/bin/python manage.py runfcgi'
                    ' host=127.0.0.1 port=8080'
                    ' daemonize=True'
                    ' minspare=1'
                    ' maxspare=%(worker_count)s'
                    ' maxchildren=1'
                    ' method=prefork'
                    ' pidfile=%(remote_dir)s/run/%(domain)s.pid' % self.env)

NginxWithFcgi = NginxFcgi
NginxServerWithFcgi = NginxFcgi

class FcgiWrapper(NginxFcgi):

    def dirs(self):
        return super(NginxFcgiWrapperCgi, self).dirs() + ['http']

    def configure(self):
        #super(NginxWithGunicorn, self).configure()

        upload_first([_('nginx/%(domain)s.fcgi.py'),
                      'fcgi/wrapper.py'],
                     _('%(remote_dir)s/http/wrapper.fcgi'),
                     fab.env,
                     mode=0755,
                     use_jinja=True)
        upload_first([_('nginx/%(domain)s.htaccess'),
                      'fcgi/.htaccess'],
                     _('%(remote_dir)s/http/.htaccess'),
                     fab.env,
                     use_jinja=True)

    def stop_backend(self):
        with fab.settings(warn_only=True):
            fab.run(_("killall -TERM wrapper.fcgi"))


    def start_backend(self):
        fab.run(_('touch %(remote_dir)s/http/wrapper.fcgi'))

class NginxWithGunicorn(NginxServer):

    backend = Gunicorn()

    def install_requirements(self):
        with fab.cd(_('%(remote_dir)s/')):
            # XXX 0.14 is buggy TODO
            fab.run('env/bin/pip install -U gunicorn')
            fab.run('env/bin/pip install -U setproctitle')

    def dirs(self):
        return super(NginxWithGunicorn, self).dirs() + ['etc/gunicorn']

    def stop_backend(self):
        with fab.settings(warn_only=True):
            fab.run(_("kill -TERM `cat %(remote_dir)s/run/gunicorn.pid`"))

    def start_backend(self):
        if fab.env.project.use_django:
            if fab.env.project.django.HAS_WSGI:
                fab.env['gunicorn_starter'] = _('gunicorn '
                                                '%(django_project_name)s.wsgi:application')
            else:
                fab.env['gunicorn_starter'] = 'gunicorn_django'
            cwd_path = _('%(django_python_path)s')
        else:
            fab.env['gunicorn_starter'] = _('gunicorn '
                                            '%(project_name)s:application')
            cwd_path = _('%(remote_dir)s/%(project_name)s')

        with fab.cd(cwd_path):
            fab.run(_('%(remote_dir)s/env/bin/%(gunicorn_starter)s'
                      ' -c %(remote_dir)s/etc/gunicorn/conf.py'))

    def configure(self):
        super(NginxWithGunicorn, self).configure()

        upload_first([_('nginx/%(domain)s.gunicorn.conf'),
                      'gunicorn/default.conf'],
                     _('%(remote_dir)s/etc/gunicorn/conf.py'),
                     fab.env,
                     use_jinja=True)


class NginxWithUwsgi(NginxServer):
    backend = UwsgiBackend()
