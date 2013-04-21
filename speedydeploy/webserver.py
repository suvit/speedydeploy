# -*- coding: utf-8 -*-
from __future__ import with_statement
import os
import time

from fabric import api as fab

from fab_deploy.utils import run_as

from base import _, Daemon, Ubuntu
from deployment import command
from utils import upload_template, upload_first


class FrontEnd(Daemon):

    config_dir = None

    namespace = 'server'

    backend = None

    def __init__(self, name, domain):
        super(FrontEnd, self).__init__(name)

        self.env = fab.env
        self.env['domain'] = domain
        self.env['server_dir'] = self.config_dir

    def enable_site(self, name):
        server_dir = self.config_dir
        fab.sudo("ln -s %(server_dir)ssites-available/%(name)s"
                 " %(server_dir)ssites-enabled/%(name)s" % locals() )

    @command
    @run_as('root')
    def enable(self):
        fab.run(_("ln -s %(server_dir)ssites-available/%(domain)s.conf"
                  " %(server_dir)ssites-enabled/%(domain)s.conf"))

    def disable_site(self, name):
        server_dir = self.config_dir
        fab.sudo("rm -f %(server_dir)ssites-enabled/%(name)s" % locals() )

    @command
    @run_as('root')
    def disable(self):
        fab.run(_("rm -f %(server_dir)ssites-enabled/%(domain)s.conf"))

    def remove_site(self, name):
        self.disable_site(name)
        server_dir = self.config_dir
        fab.sudo("rm -f %(server_dir)ssites-available/%(name)s" % locals() )

    @command
    @run_as('root')
    def remove(self):
        self.disable()
        fab.run(_("rm -f %(server_dir)ssites-available/%(domain)s.conf"))

    def install_development_libraries(self):
        if self.backend:
            self.backend.install_development_libraries()

    def install_requirements(self):
        if self.backend:
            self.backend.install_requirements()

    def dirs(self):
        dirs = []
        if self.backend:
            dirs.extend(self.backend.dirs())
        return dirs

    @command
    def start(self, pty=True):
        super(FrontEnd, self).start(pty=pty)

    @command
    def stop(self, pty=True):
        super(FrontEnd, self).stop(pty=pty)

    @command
    def restart(self, pty=True):
        super(FrontEnd, self).restart(pty=pty)

    @command
    def reload(self, pty=True):
        super(FrontEnd, self).reload(pty=pty)

    @command
    def configure(self):
        if self.backend:
            self.backend.configure()

WebServer = FrontEnd
Server = WebServer # TODO remove this


class Backend(object): #TODO inherit Server
    name = NotImplemented

    namespace = 'backend'

    def __init__(self, domain=None):
        if domain is not None:
            fab.env['domain'] = domain

        if fab.env.project.use_django:
            project_path = _('%(django_python_path)s')
        else:
            project_path = _('%(remote_dir)s/%(project_name)s')
        fab.env['project_path'] = project_path

    def start(self):
        pass

    def stop(self):
        pass


class FcgiBackend(Backend):
    name = 'fcgi'

    def install_requirements(self):
        with fab.cd(_('%(remote_dir)s/')):
            fab.run('env/bin/pip install "flup==1.0.2"')

    def stop(self):
        with fab.settings(warn_only=True):
            fab.run(_("kill -TERM `cat %(remote_dir)s/run/fcgi.pid`"))

    def start(self):
        with fab.cd(_('%(remote_dir)s/%(project_name)s')):
            # TODO use' socket=%(remote_dir)s/run/fcgi.sock'
            fab.run(_('../env/bin/python manage.py runfcgi'
                      ' host=127.0.0.1 port=8080',
                      ' daemonize=true'
                      ' minspare=1'
                      ' maxspare=%(worker_count)s'
                      ' maxchildren=%(worker_count)s'
                      ' maxrequests=10000'
                      ' method=prefork'
                      ' pidfile=%(remote_dir)s/run/fcgi.pid'
                      ' logfile=%(remote_dir)s/log/fcgi.log'))

    def reload(self):
        fab.run(_('touch %(remote_dir)s/http/wrapper.fcgi'))


class FcgiWrapper(FcgiBackend):

    fcgi_path = '%(remote_dir)s/http/'

    def dirs(self):
        return ['http']

    def configure(self):
        upload_first([_('nginx/%(domain)s-sh.fcgi'),
                      'fcgi/wrapper-sh.fcgi'],
                     _(self.fcgi_path) + 'wrapper.fcgi',
                     fab.env,
                     mode=0755,
                     use_jinja=True)

        upload_first([_('nginx/%(domain)s.fcgi'),
                      'fcgi/wrapper.fcgi'],
                     _('%(remote_dir)s/http/wrapper.fcgi'),
                     fab.env,
                     mode=0755,
                     use_jinja=True)

        upload_first([_('nginx/%(domain)s.htaccess'),
                      'fcgi/.htaccess'],
                     _('%(remote_dir)s/http/.htaccess'),
                     fab.env,
                     use_jinja=True)

        #XXX
        with fab.cd(_('%(remote_dir)s/http')):
            with fab.settings(warn_only=True):
                fab.run('ln -s ../media/static')
                fab.run('ln -s ../media/media')

    def stop(self):
        with fab.settings(warn_only=True):
            fab.run(_("killall wrapper.fcgi"))


class Gunicorn(Backend):
    name = 'gunicorn'

    namespace = 'backend'

    supervisor = False

    def dirs(self):
        return ['etc/gunicorn']

    def install_requirements(self):
        with fab.cd(_('%(remote_dir)s/')):
            fab.run('env/bin/pip install -U gunicorn')
            fab.run('env/bin/pip install -U setproctitle')

    def stop(self):
        with fab.settings(warn_only=True):
            fab.run(_("kill -TERM `cat %(remote_dir)s/run/gunicorn.pid`"))

    def start_command(self):
        if fab.env.project.use_django:
            if fab.env.project.django.HAS_WSGI:
                fab.env['gunicorn_starter'] = _('gunicorn '
                                                '%(django_project_name)s.wsgi:application')
            else:
                fab.env['gunicorn_starter'] = 'gunicorn_django'
        else:
            fab.env['gunicorn_starter'] = _('gunicorn '
                                            '%(project_name)s:application')

    def start(self):
        if self.supervisor:
            return

        self.start_command()

        with fab.cd(_('%(project_path)s')):
            fab.run(_('%(remote_dir)s/env/bin/%(gunicorn_starter)s'
                      ' -c %(remote_dir)s/etc/gunicorn/conf.py'))

    def reload(self):
        with fab.settings(warn_only=True):
            fab.run(_("kill -HUP `cat %(remote_dir)s/run/gunicorn.pid`"))

        #self.stop()
        #self.start()

    @command
    def configure(self):
        self.start_command()

        upload_first([_('gunicorn/%(domain)s.conf'),
                      _('nginx/%(domain)s.gunicorn.conf'),
                      'gunicorn/default.conf'],
                     _('%(remote_dir)s/etc/gunicorn/conf.py'),
                     fab.env,
                     use_jinja=True)

    def supervisor_configure(self):
        upload_first([_('gunicorn/%(domain)s.supervisor.conf'),
                      'gunicorn/supervisor.conf',
                     ],
                     _('%(remote_dir)s/etc/supervisor/gunicorn.conf'),
                     fab.env,
                     use_jinja=True)

    def supervisor_start(self):
        pass


class WsgiBackend(Backend):
    name = 'wsgi'

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


class UwsgiBackend(Backend):
    name = 'uwsgi'

    namespace = 'backend'

    supervisor = False

    def dirs(self):
        return ['etc/uwsgi']

    def install_requirements(self):
        with fab.cd(_('%(remote_dir)s/')):
            fab.run('env/bin/pip install -U uwsgi')
            fab.run('env/bin/pip install -U uwsgitop')

    @command
    def stop(self):
            fab.run(_("kill -INT `cat %(remote_dir)s/run/uwsgi.pid`"))

    @command
    def start(self):
        if self.supervisor:
            return

        fab.run(_('%(remote_dir)s/env/bin/uwsgi'
                  ' --ini %(remote_dir)s/etc/uwsgi/conf.ini'))

    def reload(self):
        with fab.settings(warn_only=True):
            fab.run(_("kill -HUP `cat %(remote_dir)s/run/uwsgi.pid`"))

    @command
    def configure(self):
        if fab.env.project.use_django:
            if fab.env.project.django.HAS_WSGI:
                default_template = 'uwsgi/django.ini'
            else:
                default_template = 'uwsgi/django_old.ini'
        else:
            default_template = 'uwsgi/default.ini'

        upload_first([_('uwsgi/%(domain)s.conf'),
                      _('nginx/%(domain)s.uwsgi.conf'),
                      default_template],
                     _('%(remote_dir)s/etc/uwsgi/conf.ini'),
                     fab.env,
                     use_jinja=True)

    def supervisor_configure(self):
        upload_first([_('uwsgi/%(domain)s.supervisor.conf'),
                      'uwsgi/supervisor.conf',
                     ],
                     _('%(remote_dir)s/etc/supervisor/uwsgi.conf'),
                     fab.env,
                     use_jinja=True)

    def supervisor_start(self):
        pass


class ApacheServer(FrontEnd):
    local_dir = 'apache'

    def __init__(self, **kwargs):
        kwargs.setdefault('name', 'apache')
        super(ApacheServer, self).__init__(**kwargs)


class Apache2Server(ApacheServer):

    name = 'apache'

    config_dir = '/etc/apache2/'
    sites_dir = config_dir + 'sites-available/'

    def __init__(self, **kwargs):
        kwargs.setdefault('name', 'apache2')
        super(ApacheServer, self).__init__(**kwargs)

    @run_as('root')
    def configure(self):
        upload_template(_('apache/%(domain)s.conf'),
                        fab.env.os.path.join(self.sites_dir,
                                             _('%(domain)s.conf') ),
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


class Nginx(FrontEnd):

    name = 'nginx'

    config_dir = '/etc/nginx/'
    sites_dir = config_dir + 'sites-available/'
    log_dir = '/var/log/nginx/'

    def __init__(self, **kwargs):
        kwargs.setdefault('name', 'nginx')
        super(NginxServer, self).__init__(**kwargs)

    def stop(self, pty=True):
        super(NginxServer, self).stop(pty=pty)
        self.backend_stop()

    def start(self, pty=True):
        super(NginxServer, self).start(pty=pty)
        self.backend_start()

    def backend_stop(self):
        if self.backend:
            self.backend.stop()

    def backend_start(self):
        if self.backend:
            self.backend.start()

    def backend_reload(self):
        if self.backend:
            self.backend.reload()

    def reload(self):
        self.backend_reload()

    def install_development_libraries(self):
        os = fab.env.os
        if isinstance(os, Ubuntu):
            os.install_package('python-software-properties')
            fab.run('add-apt-repository ppa:nginx/stable')
            fab.run('apt-get update')
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
    def configure(self, template=None):

        if template is None:
            template = [_('nginx/%(domain)s.conf'),
                        'nginx/default.conf']

        super(Nginx, self).configure()

        self.update_static_files() #added static_files var for fab.env

        upload_first(template,
                     fab.env.os.path.join(self.sites_dir, _('%(domain)s.conf') ),
                     fab.env,
                     use_sudo=True,
                     use_jinja=True)

        os = fab.env.os
        log_dir = os.path.join(self.log_dir, _('%(user)s'))
        os.mkdir(log_dir)
        os.change_owner(log_dir, 'www-data', 'adm')

        self.disable_site('%(domain)s.conf' % self.env)
        self.enable_site('%(domain)s.conf' % self.env)

        if hasattr(fab.env, 'logrotate'):
            fab.env.logrotate.add_script('nginx/logrotate', 'nginx')


NginxServer = Nginx
