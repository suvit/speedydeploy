#!{{ remote_dir }}/env/bin/python
# -*- coding: utf-8 -*-
import os, sys
from os.path import expanduser

os.environ['DJANGO_SETTINGS_MODULE'] = '{{django_settings}}'

os.chdir(expanduser('{{ remote_dir }}'))
sys.path.insert(0, expanduser('{{remote_dir}}/{{project_name}}'))
sys.path.insert(0, expanduser('{{django_python_path}}'))

from django.core.servers.fastcgi import runfastcgi
runfastcgi(['method=threaded',
            'daemonize=false',
            "minspare=1",
            "maxspare=1",
            "maxchildren=1",
            "maxrequests={{fcgi_maxrequests|default('1000')}}",
            "outlog={{remote_dir}}/log/fcgi.log",
            "errlog={{remote_dir}}/log/fcgi.log",
            "pidfile={{remote_dir}}/run/fcgi.pid"])
