# -*- coding: utf-8 -*-
from __future__ import with_statement
import os
import sys

from fabric import api as fab
from fabric.contrib import files as fab_files
from fabric.contrib.files import exists

from fab_deploy.crontab import crontab_set, crontab_add, crontab_show,\
    crontab_remove, crontab_update
from fab_deploy.utils import run_as

from ..base import _, Daemon
from ..deployment import command
from ..utils import upload_template, upload_first


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
