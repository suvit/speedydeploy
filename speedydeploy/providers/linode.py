from fabric import api as fab

from ..base import Ubuntu

from .base import Provider

class Linode(Provider):
    def __init__(self):
        super(Linode, self).__init__()

        fab.env.os = Ubuntu()