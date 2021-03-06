# -*- coding: utf-8 -*-
from __future__ import with_statement
import os
import sys

from fabric import api as fab
from fabric.contrib import files as fab_files
from fabric.contrib.files import exists

from fab_deploy.utils import run_as

from ..base import _, Daemon, Debian, RedHat
from ..deployment import command
from ..utils import upload_template, upload_first


class SphinxSearch(Daemon):

    use_sudo = False

    version = 'sphinx-0.9.9'
    api_version = 0x116
    # TODO attributes server host and port

    namespace = 'sphinxsearch'

    supervisor = False

    def __init__(self, daemon_name=None, configure_daemon=False, install_scripts=True):
        if daemon_name is None:
            daemon_name = _('%(project_name)s_searchd')
        super(SphinxSearch, self).__init__(daemon_name)

        self.configure_daemon = configure_daemon
        self.install_scripts = install_scripts

    def dirs(self):
        return ["data/sphinxsearch/",
                "etc/sphinxsearch/"
               ]

    @command
    def configure_daemon(self):
        upload_template('sphinxsearch/searchd',
                        _("/etc/init.d/%(project_name)s_searchd"),
                        context=fab.env,
                        use_sudo=True,
                        use_jinja=True,
                        mode=0755,
                       )

    def put_config(self):
        if not self.supervisor and self.configure_daemon:
            self.configure_daemon()

        upload_first([_("sphinxsearch/%(project_name)s.conf"),
                      "sphinxsearch/default.conf"],
                     _("%(remote_dir)s/etc/sphinxsearch/sphinx.conf"),
                     fab.env,
                     use_jinja=True)

        if self.install_scripts:
            upload_template("sphinxsearch/index_all.sh",
                            _("%(remote_dir)s/etc/sphinxsearch/index_all.sh"),
                            fab.env,
                            use_jinja=True,
                            mode=0755,
                            )

            upload_template("sphinxsearch/index_delta.sh",
                            _("%(remote_dir)s/etc/sphinxsearch/index_delta.sh"),
                            fab.env,
                            use_jinja=True,
                            mode=0755,
                            )

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
            fab.sudo('make install')
        fab.run('rm -Rf %s %s.tar.gz' % (self.version, self.version))

    def install_development_libraries(self):
        os = fab.env.os

        os.install_package('libxml2 libxml2-dev')
        os.install_package('libexpat1 libexpat1-dev')

        fab.env.db.install_headers()

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

    @command
    def configure(self, install=False, reindex=False):
        sphinx = fab.env.sphinxsearch
        if install:
            sphinx.install(reindex=reindex)
        else:
            sphinx.update(reindex=reindex)

    def supervisor_start(self, pty=False):
        pass

    def supervisor_configure(self):
        upload_first([_('sphinxsearch/%(domain)s.conf'),
                      'sphinxsearch/supervisor.conf',
                     ],
                     _('%(remote_dir)s/etc/supervisor/sphinxsearch.conf'),
                     fab.env,
                     use_jinja=True)


class SphinxSearch201(SphinxSearch):
    version = 'sphinx-2.0.1'


class SphinxSearch202(SphinxSearch201):

    version = 'sphinx-2.0.2-beta'

    use_deb = property(lambda obj: isinstance(fab.env.os, Debian))
    is_rhel = property(lambda obj: isinstance(fab.env.os, RedHat))

    def install_package(self):
        if self.use_deb:
            filename = '%s-lucid_i386.deb' %\
                       self.version.replace('sphinx', 'sphinxsearch')

            fab.run('wget http://sphinxsearch.com/files/%s' % filename)
            try:
                fab.sudo('dpkg -I %s' % filename)
            finally:
                fab.run('rm -R %s' % filename)
        elif self.is_rhel:
            fab.env.os.install_package('sphinx')
        else:
            super(self, SphinxSearch201).install_package()


class SphinxSearch203(SphinxSearch202):
    version = 'sphinx-2.0.3-release'


class SphinxSearch207(SphinxSearch202):
    version = 'sphinx-2.0.7-release'
