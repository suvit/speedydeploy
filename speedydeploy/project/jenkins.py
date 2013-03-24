# -*- coding: utf-8 -*-

from fabric import api as fab
from fabric.contrib.files import exists



class Jenkins(object):

   def install_test_reqs(self):
       fab.local('env/bin/pip install'
                 ' git+ssh://git@bitbucket.org/suvitorg/django-pwutils#egg=pwutils[tests]')

   def install_project_reqs(self, future=False):
       fab.local('env/bin/pip install -U -r requirements.txt')

       if future and fab.local.exists('requirements/future.txt'):
           fab.local('env/bin/pip install -U -r requirements/future.txt')

   def need_update(self):
       # TODO CHECK file with date
       # if date is past do update
       return True

   def test_project(self, future=False):
       fab.local('virtualenv env')

       if self.need_update():
           self.install_test_reqs()
           self.install_project_reqs(future=future)

       #fab.env.project.django.run('jenkins --settings=settings_jenkins')
       fab.local('env/bin/python manage.py jenkins --settings=settings_jenkins')
