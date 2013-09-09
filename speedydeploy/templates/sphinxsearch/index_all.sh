#/bin/sh
cd {{remote_dir}}{{vcs_repo_name}}
{{remote_dir}}env/bin/python manage.py gen_sphinx_data product --output={{remote_dir}}data/sphinxsearch/products.xml
/etc/init.d/{{project_name}}_searchd reindex
