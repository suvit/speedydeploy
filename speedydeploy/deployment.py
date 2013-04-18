# -*- coding: utf-8 -*-
from __future__ import with_statement

import inspect
import os
import sys
import time

from fabric import api as fab
from fabric.contrib import files as fab_files
from fab_deploy.system import ssh_add_key
from fab_deploy.utils import run_as

from taskset import TaskSet, task

from base import _, OS, Debian, Ubuntu, Ubuntu104, Daemon
from utils import upload_template, upload_first


def command(func=None, namespace=None, same_name=False, aliases=()):
    def decorator(view_func):
        #@wraps(view_func)
        def f(self, *args, **kwargs):

            ns_obj = getattr(fab.env, namespace, fab.env)
            return getattr(ns_obj, view_func.__name__)(*args, **kwargs)

        attr_name = '_'.join(filter(None, (namespace,
                                           view_func.__name__)))

        setattr(Deployment, attr_name, f)
        if same_name:
            setattr(Deployment, view_func.__name__, f)

        for alias in aliases:
            setattr(Deployment, alias, f)
        return view_func

    if namespace is None:
        #XXX need more clever solution
        namespace = inspect.stack()[1][0].f_locals['namespace']

    if func:
        return decorator(func)
    return decorator


class Deployment(TaskSet):

    def __init__(self):
        self.expose_to(self.__module__)

    def _is_task(self, func):
        return inspect.ismethod(func) and not func.func_name.startswith('_')

    def _task_for_method(self, method):
        return method

    def ssh_add_key(self, pub_key_file):
        """ Adds a ssh key from passed file to user's
            authorized_keys on server. """
        with open(os.path.normpath(pub_key_file), 'rt') as f:
            ssh_key = f.read()
        if fab.env.user == 'root':
            ssh_dir = '/root/.ssh'
        else:
            if 'home_dir' in fab.env:
                ssh_dir = _('%(home_dir)s/.ssh')
            else:
                ssh_dir = _('/home/%(user)s/.ssh')

        fab.env.os.mkdir(ssh_dir)
        fab_files.append('%s/authorized_keys' % ssh_dir, ssh_key)

        with fab.settings(warn_only=True): # no chmod in system
           self.set_permissions('%s/authorized_keys' % ssh_dir,
                                pattern='644')

    @run_as('root')
    def update_rsa_key(self, pub_key_file):
        """ Root adds a ssh key from passed file to user's
            authorized_keys on server."""

        self.ssh_add_key(pub_key_file)

    @run_as('root')
    def os_add_user(self):
        fab.env.os.add_user(fab.env.user)

    def add_deploy_key(self):
        fab.run('ssh-keygen -q')
        output = fab.run('cat ~/.ssh/id_rsa.pub')
        fab.local('echo %s > deploy_key' % output)

    @run_as('root')
    def add_user(self):
        self.os_add_user()
        self.update_rsa_key()

    def backup(self):
        fab.env.db.backup()
        fab.env.project.backup()

    def set_permissions(self, target=None, pattern=None):
        if target is None:
            target = '%(remote_dir)s/%(project_name)s' % fab.env

        if pattern is None:
            pattern = 'u+rwX,go+rX,go-w'

        fab.env.os.set_permissions(target=target, pattern=pattern)

    def update_env(self):
        fab.env.project.install()
        if 'provider' in fab.env and fab.env.provider.can_addpackages:
            fab.env.project.install_development_libraries()
            fab.env.project.install_setuptools()
            fab.env.project.install_virtualenv()

    def create_virtual_env(self):
        self.update_env()
        self.create_env()
        self.deploy()
        self.update_virtual_env()

    def create(self, key=None):

        if 'provider' in fab.env and fab.env.provider.can_adduser:
            if key:
                self.update_rsa_key(key) # for root

            self.os_add_user()

            if key:
                self.ssh_add_key(key)

        if fab.env.db:
            self.db_create_user(fab.env.user, fab.env.db_pass)
            self.db_create_db(fab.env.user, fab.env.user, fab.env.db_pass)

        self.create_virtual_env()

        # need setting for this
        fab.run(_('echo root > %(remote_dir)s/.forward'))

    def update(self):
        project = fab.env.project

        if project.use_django:
            project.django.reload()

        if project.use_celery:
            self.celery_configure()
        if project.use_sphinxsearch:
            self.sphinxsearch_configure()
        if project.use_memcache:
            self.memcache_configure()

        if project.use_server:
            self.server_configure()
            self.server_reload()
