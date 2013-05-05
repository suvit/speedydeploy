# -*- coding: utf-8 -*-
from __future__ import with_statement
import os

from fabric import api as fab
from fabric.contrib import files as fab_files

from fab_deploy.mysql import mysql_execute, mysql_create_user, \
    mysql_create_db, mysql_grant_permissions
from fab_deploy.utils import run_as

from base import Daemon, CommandNamespace
from deployment import command


class Database(object):
    name = None
    version = None

    namespace = 'db'
    __metaclass__ = CommandNamespace

    def execute(self, sql):
        raise NotImplementedError

    @command
    def create_user(self, user, password):
        raise NotImplementedError

    @command
    def create_db(self, db, user, password, create_user=True):
        raise NotImplementedError

    def grant_permissions(self, db, user):
        raise NotImplementedError

    def install_development_libraries(self):
        pass

    @command
    def install(self):
        self.install_development_libraries()

    @command
    def backup(self):
        pass


class DatabaseDaemon(Daemon, Database):
    pass


class SqliteDatabase(Database):
    name = 'sqlite'

    def create_user(self, user, password):
        pass

    def create_db(self, db, user, password=None, create_user=True):
        pass


class MysqlDatabase(DatabaseDaemon):
    name = 'mysql'
    version = '5.1'
    data_path = '/var/lib/mysql/'

    def __init__(self, database=None, user=None, password=None):
        super(MysqlDatabase, self).__init__('mysql')

        self.database = database
        self.user = user
        self.password = password
        self.timestamp = 1 # TODO

    def dump(self, database=None, table=None, output=None):
        context = vars(self).copy()

        if database is None:
            database == '--all-databases'
        context['database'] = database
        if table is None:
            table = ''
        context['table'] = table
        if output is None:
            output = _('/tmp/%(timestamp)_backup_%(database)s.sql')

        fab.run("mysqldump %(database)s %(table)s"
                " -u %(user)s -p%(password)s"
                " > %(output)s" % context)

    def dump2(self):
        fab.run(_("mysqldump %(database_name)s"
                  " -u %(database_user)s -p%(database_password)s"
                  " > /tmp/%(database_name)s_database.sql"))

    def hotcopy(self):
        pass

    def backup(self):
        with fab.cd(_('%(remote_dir)s/backup')):
            fab.env.os.mkdir(_("%(backup_dirname)s"))
            
            with fab.settings(warn_only=True):
                self.dump2()

    def remotecopy(self):
        fab.run(_("scp -C %(user)s@%(host)s:/tmp/%(database_production_name)s_database.sql %(database_name)s_database.sql"))

    def backup_copy(self):
        self.stop()
        try:
            fab.env.os.mkdir(_('%(remote_path)s/backup/%(backup_dir)s/'))
            fab.run(_('cp -R /var/lib/mysql/%(database)s/'
                      ' %(remote_path)s/backup/%(backup_dir)s/'))
        finally:
            self.start()
        # TODO create archive

    def restore(self):
        fab.run(_("mysql %(database_name)s"
                  " -u %(database_user)s -p%(database_password)s"
                  " < %(database_name)s_database.sql"))

    def execute(self, sql):
        mysql_execute(sql)
 
    def create_user(self, user, password):
        mysql_create_user(user, password)

    def create_db(self, db, user, password, create_user=True):
        if user != 'root' and create_user:
            self.create_user(user, password)

            # XXX
            fab.env.conf.DB_PASSWORD = password

        mysql_create_db(db, user)

    def grant_permissions(self, db, user):
        mysql_grant_permissions(db, user)

    def install_db_misc(self):
        os = fab.env.os
        os.install_package('python-mysqldb')

        # XXX needed condition here
        # bug in phpmyadmin install sql with mariadb
        # http://www.mail-archive.com/debian-bugs-closed@lists.debian.org/msg342522.html
        os.install_package('phpmyadmin')

    def install_development_libraries(self):
        os = fab.env.os
        os.install_package('mysql-server')

        self.install_db_misc()

    def install_headers(self):
        fab.env.os.install_package('libmysqlclient-dev libmysqld-dev')


class MariaDatabase(MysqlDatabase):
    name = 'mariadb'
    source_list = '''
# MariaDB repository list - created 2011-11-12 05:24 UTC
# http://downloads.askmonty.org/mariadb/repositories/
deb http://mirror2.hs-esslingen.de/mariadb/repo/%(db_version)s/ubuntu %(os_name)s main
deb-src http://mirror2.hs-esslingen.de/mariadb/repo/%(db_version)s/ubuntu %(os_name)s main'''

    def append_source(self):
        source = self.source_list % {'db_version':self.version,
                                     'os_name':fab.env.os.name,
                                    }
        if not fab_files.contains('/etc/apt/sources.list.d/mariadb.list',
                                  source):
            fab_files.append('/etc/apt/sources.list.d/mariadb.list', source)

            fab.sudo('apt-key adv --recv-keys --keyserver keyserver.ubuntu.com 1BB943DB')
            fab.sudo('apt-get update')

    def install_development_libraries(self):
        os = fab.env.os
        # TODO
        self.append_source()
        os.install_package('mariadb-server')

        self.install_db_misc()

    def install_headers(self):
        fab.env.os.install_package('libmariadbclient-dev libmariadbd-dev')

        # XXX needed to install mysql-python later
        fab.env.os.install_package('libssl-dev')


class Maria51Database(MysqlDatabase):
    version = '5.1'


class Maria52Database(MariaDatabase):
    version = '5.2'


class Maria53Database(MariaDatabase):
    version = '5.3'
