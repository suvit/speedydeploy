#!{{ remote_dir }}/env/bin/python
# -*- coding: utf-8 -*-
import os, sys
from os.path import expanduser

os.environ['DJANGO_SETTINGS_MODULE'] = '{{django_project_name}}.settings'

os.chdir(expanduser('{{ remote_dir }}'))
sys.path.insert(0, expanduser('{{django_python_path}}'))
sys.path.insert(0, expanduser('{{remote_dir}}/{{project_name}}'))

from django.core.servers.fastcgi import runfastcgi
runfastcgi(['method=prefork',
            'daemonize=false',
            "minspare=1",
            "maxspare={{worker_count|default('2')}}",
            "maxchildren=0",
            "pidfile={{remote_dir}}/run/fcgi.pid"])
