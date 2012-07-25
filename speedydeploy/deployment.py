# -*- coding: utf-8 -*-
from __future__ import with_statement

import inspect
import os
import sys
import time

from fabric import api as fab
from fabric.contrib import files as fab_files
from fab_deploy.crontab import crontab_set, crontab_add, crontab_show,\
    crontab_remove, crontab_update
from fab_deploy.system import ssh_add_key
from fab_deploy.utils import run_as

from base import _, OS, Debian, Ubuntu, Ubuntu104, Daemon
from database import *
from project.django import DjangoProject
from project import *
from server import Apache2Server, NginxServer, Apache2ServerWithFcgi,\
    Apache2ServerWithWsgi, NginxServerWithFcgi, NginxWithGunicorn
from utils import upload_template, upload_first
from vcs import *


def add_class_methods_as_module_level_functions_for_fabric(instance,
                                                           module_name):
    '''
    Utility to take the methods of the instance of a class, instance,
    and add them as functions to a module, module_name, so that Fabric
    can find and call them. Call this at the bottom of a module after
    the class definition.
    '''
    # get the module as an object
    module_obj = sys.modules[module_name]

    # Iterate over the methods of the class and dynamically create a function
    # for each method that calls the method and add it to the current module
    for method in inspect.getmembers(instance, predicate=inspect.ismethod):
        method_name, method_obj = method

        if not method_name.startswith('_'):
            # get the bound method
            func = getattr(instance, method_name)

            # add the function to the current module
            setattr(module_obj, method_name, func)

add_fabric_methods = add_class_methods_as_module_level_functions_for_fabric


class Deployment(object):

    def __init__(self):
        add_fabric_methods(self, self.__class__.__module__)

    def ssh_add_key(self, pub_key_file):
        """ Adds a ssh key from passed file to user's
            authorized_keys on server. """
        with open(os.path.normpath(pub_key_file), 'rt') as f:
            ssh_key = f.read()
        if fab.env.user == 'root':
            ssh_dir = '/root/.ssh'
        else:
            ssh_dir = _('/home/%(user)s/.ssh')

        fab.env.os.mkdir(ssh_dir)
        fab_files.append('%s/authorized_keys' % ssh_dir, ssh_key)
        self.set_permissions('%s/authorized_keys' % ssh_dir,
                             pattern='644')

    @run_as('root')
    def update_rsa_key(self, pub_key_file):
        self.ssh_add_key(pub_key_file)

    @run_as('root')
    def os_add_user(self):
        fab.env.os.add_user(fab.env.user)

    @run_as('root')
    def add_user(self):
        self.os_add_user()
        self.update_rsa_key()

    def vcs_deploy(self, force_remove=False):
        fab.env.vcs.deploy(force_remove)
    deploy = vcs_deploy

    def update_reqs(self):
        fab.env.project.update_reqs()

    def project_install(self):
        fab.env.project.install()

    def exists(self, path):
        with fab.settings(warn_only=True):
            return fab.run('test -e %s' % path)

    def install_requirements(self):
        fab.env.project.install_requirements()

    def install_development_libraries(self):
        fab.env.project.install_development_libraries()

    def install_setuptools(self):
        fab.env.project.install_setuptools()

    def install_virtualenv(self):
        fab.env.project.install_virtualenv()
        
    def backup(self):
        fab.env.db.backup()
        fab.env.project.backup()
    
    def server_restart(self):
        fab.env.server.restart()

    def server_configure(self):
        fab.env.server.configure()

    def server_reload(self):
        fab.env.server.reload()

    def memcache_configure(self, install=False):
        memcache = fab.env.memcache
        if install:
            memcache.install()
        else:
            memcache.update()

    def celery_configure(self, install=False):
        celery = fab.env.celery
        if install:
            celery.install()
        else:
            celery.update()

    def sphinxsearch_configure(self, install=False, reindex=False):
        sphinx = fab.env.sphinxsearch
        if install:
            sphinx.install(reindex=reindex)
        else:
            sphinx.update(reindex=reindex)

    def sphinxsearch_reindex(self):
        fab.env.sphinxsearch.reindex()

    def db_install(self):
        fab.env.db.install()

    def db_backup(self):
        fab.env.db.backup()

    def db_dump(self):
        fab.env.db.dump()

    def db_copy(self):
        fab.env.db.copy()

    def db_create_db(self, name, password=None):
        db = fab.env.db
        db.create_db(name, name, password)

    def db_create_user(self, user, password):
        db = fab.env.db
        db.create_user(user, password)

    def db_update(self):
        fab.env.db.update()

    def celery_restart(self):
        fab.env.celery.restart()

    def scrapy_configure(self):
        fab.env.project.scrapy.configure()

    def django_update_settings_local(self):
        fab.env.project.django.update_settings_local()
    #XXX
    update_settings_local = django_update_settings_local

    def set_permissions(self, target=None, pattern=None):
        if target is None:
            target = '%(remote_dir)s/%(project_name)s' % fab.env
        
        if pattern is None:
            pattern = 'u+rwX,go+rX,go-w'

        fab.env.os.set_permissions(target=target, pattern=pattern)

    def update_env(self):
        fab.env.project.install_development_libraries()
        fab.env.project.install_setuptools()
        fab.env.project.install_virtualenv()
        fab.env.project.install()

    def create_env(self):
        fab.env.project.create_env()
    
    def update_virtual_env(self):
        fab.env.project.install_requirements()

    def create_virtual_env(self):
        self.update_env()
        self.create_env()
        self.deploy()
        self.update_virtual_env()

    def django_deploy_static(self):
        fab.env.project.django.deploy_static()

    def supervisor_configure(self, install=False):
        supervisor = fab.env.project.supervisor
        if install:
            supervisor.install()
        else:
            supervisor.update()
