SPHINX_API_VERSION = {{sphinxsearch.api_version|default('0x116')}}
SPHINX_ROOT = "/home/{{user}}/data/sphinxsearch/"
SPHINX_SERVER = "{{sphinxsearch.host|default("/home/%s/run/searchd.sock" % user)}}"
SPHINX_PORT = {{sphinxsearch.port|default(None)}}
