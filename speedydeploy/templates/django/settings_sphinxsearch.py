SPHINX_API_VERSION = {{sphinxsearch.api_version|default('0x116')}}
SPHINX_ROOT = "{{sphinxsearch.host|default('localhost')}}"
SPHINX_HOST = "/home/{{user}}/run/searchd.sock"
SPHINX_PORT = {{sphinxsearch.port|default('11312')}}
