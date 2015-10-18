# -*- coding: utf-8 -*-
from __future__ import with_statement

from fabric import api as fab
from fabric.contrib.files import exists

from fab_deploy.utils import run_as

from base import _, Daemon
from deployment import command


class VCS(object):

    def __init__(self):
        if 'vcs_repo_name' not in fab.env:
            fab.env['vcs_repo_name'] = fab.env['project_name']

    def install_development_libraries(self):
        pass

    @command(namespace='vcs', aliases=('deploy',))
    def deploy(self, force_remove=False):
        if exists(_('%(remote_dir)s/%(vcs_repo_name)s')) and not force_remove:
            with fab.cd(_('%(remote_dir)s/%(vcs_repo_name)s/')):
                self.update()
        else:
            with fab.cd(_('%(remote_dir)s/')):
                with fab.settings(warn_only=True):
                    fab.run(_("rm -rf %(vcs_repo_name)s"))
                    self.clone()
        with fab.cd(_('%(remote_dir)s/%(vcs_repo_name)s/')):
           self.remove_pyc()

    def export(self):
        raise NotImplementedError

    def update(self):
        raise NotImplementedError

    def clone(self):
        raise NotImplementedError

    # TODO remove to OS class
    def remove_pyc(self): # TODO use fab_utils remove_pyc
        """ Deletes *.pyc files from project source dir """
        fab.run("find . -name '*.pyc' -delete")


class SVN(VCS):
    def find_last_rev(self):
        out = fab.local(_('svn log -ql1 %(svn_repo)s/%(vcs_repo_name)s'),
                        capture=True)
        return out.split()[1].strip('r')

    def install_development_libraries(self):
        fab.env.os.install_package('subversion')

    def export(self):
        # TODO svn_rev svn_path move to self attrs
        fab.local("mkdir tmp")
        fab.local(_("svn export -r %(svn_rev)s %(svn_path)s ./tmp/%(vcs_repo_name)s"))

    def update(self):
        fab.run('svn up')

    def clone(self):
        fab.run(_('svn checkout -r %(svn_rev)s %(svn_path)s %(vcs_repo_name)s'))


class SVNServer(object):

    # TODO added templates for hooks (post-commit and etc)
    def install_development_libraries(self):
        os = fab.env.os
        os.install_package('libsvn-notify-perl')
        os.install_package('postfix') # for sendmail


class GIT(VCS):

    @property
    def use_submodules(self):
        return exists(_('%(remote_dir)s/%(vcs_repo_name)s/.gitmodules'))

    def install_development_libraries(self):
        fab.env.os.install_package('git-core')

    def export(self):
        fab.local("mkdir tmp")
        fab.local(_("git clone ./tmp/%(vcs_repo_name)s"))

    def update(self):
        fab.run('git pull')
        if self.use_submodules:
            fab.run('git submodule update --init')

    def clone(self):
        repo_name = fab.env.get('vcs_repo_name') or ''
        fab.run(_('git clone --recursive %(git_path)s') + ' ' + repo_name)
        #if self.use_submodules:
        #    with fab.cd(_('%(remote_dir)s/%(vcs_repo_name)s/')):
        #        fab.run('git submodule init')
        #        fab.run('git submodule update')


class HG(VCS):
    def install_development_libraries(self):
        fab.env.os.install_package('mercurial')


class NoneVCS(VCS): # MockObject For no version control
    # TODO use fab_utils here
    pass


class NoneVCSWithExport(NoneVCS):
    def __init__(self, vcs):
        self.vcs = vcs

    def install_development_libraries(self):
        self.vcs.install_development_libraries()

    def export(self):
        self.vcs.export()

    def clear(self):
        with fab.cd(_('%(remote_dir)s')):
            fab.env.os.rm("build")
        fab.local("rm -rf tmp/")

    def prepare(self):
        fab.local(_("cd tmp/ && tar -czf %(vcs_repo_name)s.tgz %(vcs_repo_name)s"))
        fab.put(_('tmp/%(vcs_repo_name)s.tgz'), _('%(remote_dir)s/tmp/'))

        with fab.cd(_('%(remote_dir)s/tmp')):
            fab.run(_("tar -xzf %(remote_dir)s/tmp/%(vcs_repo_name)s.tgz"))

        with fab.cd(_('%(remote_dir)s')):
            fab.env.os.mkdir("build")
            fab.run(_("mv %(remote_dir)s/tmp/%(vcs_repo_name)s build"))

    def deploy_old(self):
        if not getattr(fab.env, 'debug', False):
            self.clear()
        try:
            self.export()
            self.prepare()
        finally:
            if not getattr(fab.env, 'debug', False):
                fab.local("rm -rf tmp/")

    def install_project(self):
        with fab.cd(_('%(remote_dir)s')):
            try:
                with fab.settings(warn_only=True):
                    fab.run(_("rm -rf %(vcs_repo_name)s"))
                    fab.run(_("mv build/%(vcs_repo_name)s %(vcs_repo_name)s"))
            finally:
                fab.run("rm -rf build")
        fab.env.os.set_permissions()

    def deploy(self, force_remove=False):
        self.deploy_old()
        self.install_project()


class Bazaar(VCS):
    def install_development_libraries(self):
        fab.env.os.install_package('bzr')
