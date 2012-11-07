# -*- coding: utf-8 -*-
from __future__ import with_statement
import os
import sys

from fabric import api as fab
from fabric.contrib import files as fab_files

from fab_deploy.utils import run_as

from ..base import _, Daemon, Ubuntu
from ..deployment import command
from ..utils import upload_template, upload_first


class Redis(Daemon):
    pass