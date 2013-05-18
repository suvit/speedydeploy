
from fabric import api as fab


class Php(object):
    def install(self):
        fab.sudo('apt-get install php5-fpm')


class PhpMyAdmin(object):
    def install(self):
        fab.sudo('apt-get install php5-mysql phpmyadmin -y')
        with fab.cd('/usr/share/nginx/www'):
            fab.sudo('ln -s /usr/share/phpmyadmin')
