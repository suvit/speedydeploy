

from .base import ObjectWithCommand
        

# TODO inherit daemon
class NewRelic(ObjectWithCommand):
    namespace = 'newrelicd'
 
    license_key = None

    @command
    def install(self):
        # XXX for Debian only

        fab.sudo('wget -O /etc/apt/sources.list.d/newrelic.list http://download.newrelic.com/debian/newrelic.list')
        fab.sudo('apt-key adv --keyserver hkp://subkeys.pgp.net --recv-keys 548C16BF')

        fab.sudo('apt-get update')
        fab.sudo('apt-get install newrelic-sysmond')

        fab.sudo('nrsysmond-config --set license_key=%s' % self.license_key)

    @command
    def start(self):
        fab.sudo('/etc/init.d/newrelic-sysmond start')


class NewRelicApp(ObjectWithCommand):
    namespace = 'newrelic'
 
    license_key = None

    def install_development_libraries(self):
        fab.sudo('pip install -U newrelic')

        fab.run('newrelic-admin generate-config %s etc/newrelic/newrelic.ini' % self.license_key)

    @command
    def configure(self):
        fab.run('newrelic-admin')

        
 
