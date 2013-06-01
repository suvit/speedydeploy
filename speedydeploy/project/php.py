
from fabric import api as fab


class Php(object):
    def install(self):
        fab.sudo('apt-get install php5-fpm')
        # limit worker count
        # You should have "cgi.fix_pathinfo = 0;" in php.ini



class PhpMyAdmin(object):
    def install(self):
        fab.sudo('apt-get install php5-mysql phpmyadmin -y')
        with fab.cd('/usr/share/nginx/html'):
            fab.sudo('ln -s /usr/share/phpmyadmin')
