# -*- coding: utf-8 -*-
from __future__ import with_statement
import os
import posixpath as os_path
import ntpath as nt_path
from functools import wraps

from fabric import api as fab
from fabric.context_managers import hide
from fabric.contrib import files as fab_files

from fab_deploy.utils import run_as, detect_os

_ = lambda s: s % fab.env

class CommandNamespace(type):

    _registry = {}

    def __new__(cls, name, bases, attrs):
        new_class = super(CommandNamespace,
                     cls).__new__(cls, name, bases, attrs)
        cls.register(new_class)
        return new_class

    @classmethod
    def register(cls, ns_class):
        cls._registry[ns_class.namespace] = ns_class

    @classmethod
    def get(cls, name):
        return cls._registry.get(name)


class ObjectWithCommands(object):
    namespace = None
    __metaclass__ = CommandNamespace


class OS(object):

    name = NotImplemented
    version = None
    arch = 32

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


class Unix(OS):

    def rm(self, command):
        return fab.run('rm -rf %s' % command)

    def mkdir(self, command):
        return fab.run('mkdir -p %s' % command)

    def set_permission(self, target, pattern):
        user = fab.env['user']
        self.change_owner(target, user, user)
        self.change_mode(target, pattern)

    def set_permissions(self, target=None, pattern=None):

        if target is None:
            target = '%(remote_dir)s/%(project_name)s/' % context

        if pattern is None:
            pattern = 'u+rwX,go+rX,go-w'

        user = fab.env['user']
        self.change_owner(target, user, user)

        fab.run('chmod -R %(pattern)s %(target)s' % locals() )

    @run_as('root')
    def change_owner(self, target, user, group):
        fab.run('chown -R %(user)s:%(group)s %(target)s' % locals())

    @run_as('root')
    def change_mode(self, target, pattern):
        fab.run('chmod -R %(pattern)s %(target)s' % locals() )


class Linux(Unix):
    pass


class Debian(Linux):

    def install_package(self, package):
        return fab.sudo('apt-get install -q -y %s' % package)

    def add_user(self, user):
        return fab.sudo('adduser %s' % user)

    def del_user(self, user):
        return fab.sudo('deluser %s' % user)

    @run_as('root')
    def install_development_libraries(self):
        super(Debian, self).install_development_libraries()
        self.install_package('sudo')


class Gentoo(Linux):
    pass


class FreeBSD(Unix):
    pass


class EtchDebian(Debian):
    name = 'etch'
    version = '4.0'


class LennyDebian(Debian):
    name = 'lenny'
    version = '5.0'


class SqueezeDebian(Debian):
    name = 'squeeze'
    version = '6.0'


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


class Ubuntu1110(Ubuntu):
    name = 'oneiric'
    version = '11.10'


class Ubuntu124(Ubuntu):
    name = 'precise'
    version = '12.4'


class Ubuntu124x64(Ubuntu124):
    name = 'precise'
    version = '12.4'
    arch = 64


class SentOS(Linux):
    pass


class SentOS64(Linux):
    arch = 64


class Windows(OS):
    path = nt_path

    def rm(self, command):
        return fab.run('del -f %s' % command)


class WindowsXP(Windows):
    name = 'xp'
    version = '5.1'


class Windows7(Windows):
    name = '7'
    version = '7.0'


class Windows8(Windows):
    name = '8'
    version = '8.0'


class Daemon(object):

    namespace = None
    __metaclass__ = CommandNamespace

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

    def restart(self, pty=True):
        with fab.settings(warn_only=True):
            self.stop(pty=pty)
        self.start(pty=pty)

    @run_as('root')
    def status(self):
        fab.run("%s %s status" % (self.os.daemon_restarter, self.name))
