from fabric import api as fab
from fabric.contrib import files

from ..base import Ubuntu, Ubuntu124, Ubuntu124x64
from ..deployment import _, command
from ..project.cron import CronTab
from ..project import LogRotate

from .base import Provider


class DigitalOcean(Provider):

    namespace = 'digitalocean'
    def __init__(self):
        super(DigitalOcean, self).__init__()

        fab.env.os = Ubuntu124x64()

        fab.env.remote_dir = _("/home/%(user)s/")
        fab.env.home_dir = _("/home/%(user)s/")

        fab.env.cron = CronTab()
        fab.env.logrotate = LogRotate()

    @command
    def add_swap(self):
        # https://www.digitalocean.com/community/articles/how-to-add-swap-on-ubuntu-12-04
        fab.sudo('dd if=/dev/zero of=/swapfile bs=1024 count=512k')
        fab.sudo('mkswap /swapfile')
        fab.sudo('swapon /swapfile')
        fab.sudo('chown root:root /swapfile')
        fab.sudo('chmod 0600 /swapfile')

        files.append('/etc/fstab',
                     '/swapfile       none    swap    sw      0       0',
                     use_sudo=True)


class Droplet(DigitalOcean):
    pass


class Droplet1(Droplet):
    pass


class Droplet2(Droplet):
    pass
