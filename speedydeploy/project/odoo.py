# -*- coding: utf-8 -*-
from __future__ import with_statement

from fabric import api as fab

from ..base import _
from ..deployment import command

class OpenErp(object):
    version = (0, 7)


class Odoo(OpenErp):
    version = (0, 8)

    namespace = 'odoo'

    def install_development_libraries(self):
        #fab.env.os.install_package('python-dev')
        # common install_development_libraries

        # db
        fab.env.os.install_package('postgresql libpq-dev')

        # lxml
        fab.env.os.install_package('libxml2-dev libxslt-dev')

        # ldap
        fab.env.os.install_package('libldap2-dev libsasl2-dev')

    @command
    def install(self):
        #self.install_development_libraries()
        # install_virtualenv
        #

        fab.run('~/env/bin/pip install --process-dependency-links -e git+https://github.com/odoo/odoo@8.0#egg=odoo_8')


