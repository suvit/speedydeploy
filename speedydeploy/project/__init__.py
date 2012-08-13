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
    def configure(self, isnstall=True):
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


class RabbitMQ(Daemon):
    def __init__(self, daemon_name=None):
        if daemon_name is None:
            daemon_name = 'rabbitmq-server'
        super(RabbitMQ, self).__init__(daemon_name)

    @run_as('root')
    def install_development_libraries(self):
        os = fab.env.os
        os.install_package('rabbitmq-server')

        fab.run(_('rabbitmqctl add_user %(user)s %(mq_pass)s'))
        fab.run(_('rabbitmqctl add_vhost %(domain)s'))
        fab.run(_('rabbitmqctl set_permissions'
                  ' -p %(domain)s %(user)s'
                  ' ".*" ".*" ".*"'))


class Celery(Daemon):

    broker = None

    namespace = 'celery'

    def __init__(self, daemon_name=None):
        if daemon_name is None:
            daemon_name = _('%(instance_name)s_celeryd')
        super(Celery, self).__init__(daemon_name)

    def dirs(self):
        return ['etc/celery']

    @run_as('root')
    def put_config(self):

        upload_template('celery/celeryd',
                        _("/etc/init.d/%(instance_name)s_celeryd"),
                        context=fab.env,
                        use_sudo=True,
                        use_jinja=True,
                        mode=0755,
                       )

        upload_template('celery/celeryd.conf',
                        _("%(remote_dir)s/etc/celery/"),
                        context=fab.env,
                        use_jinja=True,
                       )

    @run_as('root')
    def install(self):
        self.put_config()

        #fab.sudo(_("chown %(user)s:%(user)s %(remote_dir)s/etc/celery/"))

        with fab.settings(warn_only=True):
            self.stop()
        self.start()

    def update(self):
        self.put_config()
        self.restart()

    @command
    def configure(self, install=False):
        celery = fab.env.celery
        if install:
            celery.install()
        else:
            celery.update()

    @run_as('root')
    def install_development_libraries(self):
        os = fab.env.os
        if self.broker:
            self.broker.install_development_libraries(self)
        os.install_package('rabbitmq-server')

    @command
    def restart(self):
        return super(Celery, self).restart()


class SphinxSearch(Daemon):

    version = 'sphinx-0.9.9'
    api_version = 0x116
    # TODO attributes server host and port

    namespace = 'sphinxsearch'

    def __init__(self, daemon_name=None):
        if daemon_name is None:
            daemon_name = _('%(instance_name)s_searchd')
        super(SphinxSearch, self).__init__(daemon_name)

    def dirs(self):
        return ["data/sphinxsearch/",
                "etc/sphinxsearch/"
               ]

    @run_as('root')
    def put_config(self):
        upload_template("sphinxsearch/sphinx.conf",
                        _("%(remote_dir)s/etc/sphinxsearch/sphinx.conf"),
                        fab.env,
                        use_jinja=True)

        # common template
        upload_template('sphinxsearch/searchd',
                        _("/etc/init.d/%(instance_name)s_searchd"),
                        context=fab.env,
                        use_sudo=True,
                        use_jinja=True,
                        mode=0755,
                       )

        upload_template("sphinxsearch/index_all.sh",
                        _("%(remote_dir)s/etc/sphinxsearch/index_all.sh"),
                        fab.env,
                        use_jinja=True,
                        mode=0755,
                        )

    @run_as('root')
    def install_package(self):
        #fab.env.os.install_package('sphinxsearch')
        fab.run('wget http://sphinxsearch.com/files/%s.tar.gz' % self.version)
        fab.run('tar -xzf %s.tar.gz' % self.version)
        with fab.cd('%s' % self.version):
            configure = './configure'
            if fab.env.db.name != 'mysql':
                configure += ' --without-mysql'
            fab.run(configure)
            fab.run('make')
            fab.run('make install')
        fab.run('rm -Rf %s %s.tar.gz' % (self.version, self.version))

    @run_as('root')
    def install_development_libraries(self):
        os = fab.env.os

        os.install_package('libxml2 libxml2-dev')
        os.install_package('libexpat1 libexpat1-dev')

        fab.env.db.install_headers()

    @run_as('root')
    def install(self, reindex=False):
        with fab.settings(warn_only=True):
            self.stop()

        self.install_development_libraries()
        self.install_package()

        self.put_config()
        
        if reindex:
            self.reindex()

        self.start()

    def update(self, reindex=False):
        self.put_config()

        if reindex:
            self.reindex()

        self.restart()

    def update_cron(self):
        fab.env.setdefault('sphinxsearch_time', '10 *')
        fab.env.cron.update(_('%(sphinxsearch_time)s * * *'
                              ' %(remote_dir)s/etc/sphinxsearch/index_all.sh'
                              ' >> /home/%(user)s/log/searchd_reindex.log'),
                            marker='sphinx_reindex')

    @command
    def reindex(self, pty=True):
        fab.run(_("%(remote_dir)s/etc/sphinxsearch/index_all.sh"))
        fab.run("%s %s reindex" % (self.os.daemon_restarter, self.name), pty=pty)

    @command
    def configure(self, install=False, reindex=False):
        sphinx = fab.env.sphinxsearch
        if install:
            sphinx.install(reindex=reindex)
        else:
            sphinx.update(reindex=reindex)


class SphinxSearch201(SphinxSearch):
    version = 'sphinx-2.0.1'


class SphinxSearch202(SphinxSearch201):

    version = 'sphinx-2.0.2-beta'

    use_deb = property(lambda: isinstance(fab.env.os, Ubuntu))

    @run_as('root')
    def install_package(self):
        if self.use_deb:
            filename = '%s-lucid_i386.deb' %\
                       self.version.replace('sphinx', 'sphinxsearch')

            fab.run('wget http://sphinxsearch.com/files/%s' % filename)
            try:
                fab.run('dpkg -I %s' % filename)
            finally:
                fab.run('rm -R %s' % filename)
        else:
            super(self, SphinxSearch201).install_package()


class SphinxSearch203(SphinxSearch202):

    version = 'sphinx-2.0.3-release'


class LogRotate(object):

    config_dir = '/etc/logrotate.d'

    def add_script(self, file_name):
        fab.put(file_name,
                fab.env.os.path.join(self.config_dir,
                                     _('%(user)s')),
                use_sudo=True)


class CronTab(object):

    namespace = 'crontab'

    def set(self, content):
        crontab_set(content)

    def show(self):
        crontab_show()

    def add(self, content, marker=None):
        crontab_add(content, marker)

    def remove(self, marker):
        crontab_remove(marker)

    def update(self, content, marker):
        crontab_update(content, marker)

    def add_many(self, tabs):
        pass# TODO

    def update_many(self, tabs):
        pass # TODO

    def remove_many(self, markers):
        pass# TODO


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


class SuperVisor(Daemon):

    config_dir = '/etc/supervisor/'
    use_gunicorn = False
    use_celery = False
    use_sphinxsearch = False

    namespace = 'supervisor'

    def __init__(self, daemon_name=None):
        if daemon_name is None:
            daemon_name = 'supervisord'
        super(SuperVisor, self).__init__(daemon_name)
        self.listerners = []

    def dirs(self):
        return ['etc/supervisor']

    @run_as('root')
    def install_development_libraries(self):
        fab.env.os.install_package('supervisor')

    @run_as('root')
    def configure_daemon(self):
        upload_template(_('supervisor/supervisord.conf'),
                        _('%(remote_path)s/etc/supervisor/%(domain)s.conf'),
                        fab.env,
                        use_jinja=True)


    def install(self):
        self.configure_daemon()
        upload_template(_('supervisor/%(domain)s.conf'),
                        fab.env.os.path.join(self.config_dir,
                                             _('%(domain)s.conf')),
                        fab.env,
                        use_jinja=True)

        #for item in self.manage:
        #    item.configure_supervisor()

    @command
    def configure(self, install=False):
        supervisor = fab.env.project.supervisor
        if install:
            supervisor.install()
        else:
            supervisor.update()


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

    use_supervisor = property(lambda self: hasattr(self, 'supervisor'))
    use_scrapy = property(lambda self: hasattr(self, 'scrapy'))
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
