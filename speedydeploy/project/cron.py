# -*- coding: utf-8 -*-
from __future__ import with_statement
import os
import sys

from fabric import api as fab
from fabric.contrib import files as fab_files
from fabric.contrib.files import exists

from fab_deploy.crontab import (crontab_set, _get_current,
                                _marker)
from fab_deploy.utils import run_as

from ..base import _, Daemon
from ..deployment import command
from ..utils import upload_template, upload_first


class CronTab(object):

    namespace = 'cron'

    def set(self, content):
        crontab_set(content)

    @command(aliases=('cron_show',))
    def get(self, hide_stdout=True):
        return _get_current()

    def add(self, content, marker=None):
        old_crontab = self.get(hide_stdout=True)
        marker = _marker(marker)
        self.set(old_crontab + '\n' + content + marker)
        return marker

        add_line(content, marker)

    def remove(self, marker):
        """ Removes a line added and marked using add_line. """
        marker = _marker(marker)
        lines = [line for line in self.get(hide_stdout=True).splitlines()
                 if line and not line.endswith(marker)]
        self.set("\n".join(lines))

    def update(self, content, marker):
        """ Adds or updates a line in crontab. """
        self.remove(marker)
        return self.add(content, marker)

    @command
    def clear(self):
        fab.run('crontab -r')

    def add_many(self, tabs):
        pass# TODO

    def update_many(self, tabs):
        pass # TODO

    def remove_many(self, markers):
        pass# TODO


class BCronTab(CronTab):
    def set(self, content):
        fab.run("echo '%s' > ~/.cronjobs" % content)
        try:
            fab.run("crontab ~/.cronjobs")
        finally:
            fab.run("rm ~/.cronjobs")
