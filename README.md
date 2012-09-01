
Installing
==========

1. ```pip install speedydeploy```

2. create ```deploy``` dir in your project. and added fabfile.py to it.

Example fabfile.py:

```python
# -*- coding: utf-8 -*-
import os
import sys

import fabric.api as fab

from fab_deploy import update_env as fab_update_env, run_as

from speedydeploy.deployment import _, Deployment
from speedydeploy.project import (CronTab, Project, SphinxSearch,
                                  SuperVisor, SuperVisorD)
from speedydeploy.project.django import DjangoProject
from speedydeploy.base import Ubuntu104
from speedydeploy.database import MysqlDatabase
from speedydeploy.server import Nginx, Gunicorn
from speedydeploy.vcs import SVN


class PersonaProduction(Deployment):

    def node4(self):
        fab.env.hosts = ["persona@node4.hidden.ru"]
        fab.env.user = "persona"

        fab.env.project_name = "personashop"
        fab.env.remote_dir = _("/home/%(user)s")
        fab.env.instance_name = fab.env.user

        fab.env.os = Ubuntu104()
        fab.env.cron = CronTab()
        fab.env.project = Project()
        fab.env.project.django = DjangoProject(_('%(remote_dir)s/%(project_name)s/'),
                                               _('settings/settings_%(user)s.py')
                                              )

        fab.env.server = Nginx(domain='www.persona1.ru')
        fab.env.domain_aliases = ['persona1.ru']

        fab.env.backend = fab.env.server.backend = Gunicorn()
        fab.env.worker_count = 1

        fab.env.db = MysqlDatabase()
        fab.env.db_pass = 'hidden'

        fab.env.vcs = SVN()
        fab.env.svn_path = 'https://code.hidden.ru/path/to/project/'
        fab.env.svn_rev = 'HEAD'

        fab.env.supervisor = SuperVisor()
        fab.env.supervisor.watch(fab.env.backend)

        fab_update_env()

    def update_cron(self):
        context = dict(python_path=_('%(remote_dir)s/env/bin/python'),
                       manage_path=_('%(remote_dir)s/%(project_name)s/manage.py'),
                       project_path=_('%(remote_dir)s'),
                      )

        crontab = fab.env.cron

        crontab.update('0 4 * * * %(python_path)s %(manage_path)s cleanup' % context,
                       marker='cleanup')

        crontab.update('*/5 * * * * %(python_path)s %(manage_path)s send_mail' % context,
                       marker='send_mail')

        crontab.update('20 7-21/2 * 1-5 %(python_path)s %(manage_path)s yandex_export' % context,
                       marker='yandex_export')

instance = PersonaProduction()

```

3. run ```fub node4 create``` TODO
