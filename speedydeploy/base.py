# -*- coding: utf-8 -*-
from __future__ import with_statement
import os
import posixpath as os_path
import ntpath as nt_path

from fabric import api as fab
from fabric.contrib import files as fab_files

from fab_deploy import detect_os
from fab_deploy.utils import run_as

_ = lambda s: s % fab.env


class FabricNamespace(object):
    namespace = None
    methods = ()


class OS(object):

    name = NotImplemented
    version = None

    registry = {}
    daemon_restarter = 'invoke-rc.d'

    path = os_path

    @classmethod
    def detect_os(cls):
        os_name = detect_os()
        os_class = OS.registry.get(os_name, OS)
        os = os_class()
        fab.env.os = os

    @run_as('root')
    def install_package(self, package):
        raise NotImplementedError()

    @run_as('root')
    def install_development_libraries(self):
        # must have to compile mysql and etc
        self.install_package('python-dev')


class Linux(OS):

    @run_as('root')
    def set_permission(self, target, pattern):
        # XXX
        fab.env['target'] = target
        fab.env['pattern'] = pattern

        fab.run(_('chown %(user)s:%(user)s %(target)s -R'))
        fab.run(_('chmod %(pattern)s %(target)s -R'))

    @run_as('root')
    def set_permissions(self, target=None, pattern=None):
        context = fab.env

        if target is None:
            target = '%(remote_dir)s/%(project_name)s' % context
        context['target'] = target

        if pattern is None:
            pattern = 'u+rwX,go+rX,go-w'
        context['pattern'] = pattern

        fab.sudo('chown %(user)s:%(user)s %(target)s -R' % context)
        fab.sudo('chmod %(pattern)s %(target)s -R' % context )


class Debian(Linux):

    def rm(self, command):
        return fab.run('rm -rf %s' % command)

    def mkdir(self, command):
        return fab.run('mkdir -p %s' % command)

    def install_package(self, package):
        return fab.sudo('apt-get install -y %s' % package)

    def add_user(self, user):
        return fab.sudo('adduser %s' % user)

    def del_user(self, user):
        return fab.sudo('deluser %s' % user)

    @run_as('root')
    def install_development_libraries(self):
        self.install_package('sudo')


class FreeBSD(OS):

    def rm(self, command):
        with fab.settings(
            fab.context_managers.hide('warnings'),
            warn_only=True):
            fab.run('rm -rf %s' % command)

    def mkdir(self, command):
        with fab.settings(
            fab.context_managers.hide('warnings'),
            warn_only=True):
            fab.run('mkdir -p %s' % command)


class EtchDebian(Debian):
    name = 'etch'
    version = '4.0'


class LennyDebian(Debian):
    name = 'lenny'
    version = '5.0'


class Ubuntu(Debian):
    daemon_restarter = 'service'


class Ubuntu104(Ubuntu):
    name = 'lucid'
    version = '10.4'


class Ubuntu1010(Ubuntu):
    name = 'maverick'
    version = '10.10'


class Ubuntu114(Ubuntu):
    name = 'natty'
    version = '11.4'


class Windows(OS):
    path = nt_path

    def rm(self, command):
        return fab.run('del -f %s' % command)


class WindowsXP(Windows):
    name = 'xp'
    version = '5.1'


class Daemon(object):

    def __init__(self, daemon_name, os=None):
        if os is None:
            os = fab.env.os
        self.name = daemon_name
        self.os = os

    @run_as('root')
    def start(self, pty=True):
        fab.run("%s %s start" % (self.os.daemon_restarter, self.name), pty=pty)

    @run_as('root')
    def stop(self, pty=True):
        fab.run("%s %s stop" % (self.os.daemon_restarter, self.name), pty=pty)

    # don`t use restart cause it fails when service not running
    def restart(self, pty=True):
        with fab.settings(warn_only=True):
            self.stop(pty=pty)
        self.start(pty=pty)

    @run_as('root')
    def status(self):
        fab.run("%s %s status" % (self.os.daemon_restarter, self.name))
