#!/usr/bin/python2.5
# django wrapper

import os, sys
from os.path import expanduser

os.environ['DJANGO_SETTINGS_MODULE'] = '{{project_name}}.settings'

os.chdir(expanduser('~'))
sys.path.insert(1, expanduser('~/{{project_name}}'))

from django.core.servers.fastcgi import runfastcgi
runfastcgi(['method=prefork',
            'daemonize=false',
            "minspare=1",
            "maxspare={{worker_count}}",
            "maxchildren=0",
            "maxrequests={{ backend_max_requests|default('10000') }}",
           ])
