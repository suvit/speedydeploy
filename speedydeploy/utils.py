# -*- coding: utf-8 -*-
from __future__ import with_statement
import os

from fabric.operations import run, sudo, put
from fabric.context_managers import settings, hide
from fabric.utils import abort
from fabric.contrib.files import exists
from StringIO import StringIO


class DeployTemplateNotFound(Exception):
    def __init__(self, name, message=None):
        self.name = name
        self.message = message

    def __repr__(self):
        return 'NotFound: ' + repr(self.name)
 
    def __str__(self):
        return '%s %s' % (super(DeployTemplateNotFound, self), self.name)


common_template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                   'templates')
                                     )


def render_template(filename, context=None, use_jinja=False, template_dir=None):
    text = None
    if use_jinja:
        try:
            from jinja2 import Environment, FileSystemLoader, ChoiceLoader
            from jinja2.exceptions import TemplateNotFound

            dirs = ['.', common_template_dir]
            if template_dir:
                dirs.insert(0, template_dir)
            loader = FileSystemLoader(dirs)

            jenv = Environment(loader=loader)
            try:
                text = jenv.get_template(filename).render(**context or {})
            except TemplateNotFound, err:
                raise DeployTemplateNotFound(err.name, err.message)
            text = text.encode('utf8')
        except ImportError, e:
            abort("tried to use Jinja2 but was unable to import: %s" % e)
    else:
        # TODO add template dir
        try:
            with open(filename) as inputfile:
                text = inputfile.read()
        except IOError:
            raise DeployTemplateNotFound(filename) 
        if context:
            text = text % context
    return text

# patched version to support urf-8 in template
def upload_template(filename, destination, context=None, use_jinja=False,
    template_dir=None, use_sudo=False, backup=True, mirror_local_mode=False,
    mode=None):
    """
    Render and upload a template text file to a remote host.

    ``filename`` should be the path to a text file, which may contain `Python
    string interpolation formatting
    <http://docs.python.org/release/2.5.4/lib/typesseq-strings.html>`_ and will
    be rendered with the given context dictionary ``context`` (if given.)

    Alternately, if ``use_jinja`` is set to True and you have the Jinja2
    templating library available, Jinja will be used to render the template
    instead. Templates will be loaded from the invoking user's current working
    directory by default, or from ``template_dir`` if given.

    The resulting rendered file will be uploaded to the remote file path
    ``destination``.  If the destination file already exists, it will be
    renamed with a ``.bak`` extension unless ``backup=False`` is specified.

    By default, the file will be copied to ``destination`` as the logged-in
    user; specify ``use_sudo=True`` to use `sudo` instead.

    The ``mirror_local_mode`` and ``mode`` kwargs are passed directly to an
    internal `~fabric.operations.put` call; please see its documentation for
    details on these two options.

    .. versionchanged:: 1.1
        Added the ``backup``, ``mirror_local_mode`` and ``mode`` kwargs.
    """
    func = use_sudo and sudo or run
    # Normalize destination to be an actual filename, due to using StringIO
    with settings(hide('everything'), warn_only=True):
        if func('test -d %s' % destination).succeeded:
            sep = "" if destination.endswith('/') else "/"
            destination += sep + os.path.basename(filename)

    # Use mode kwarg to implement mirror_local_mode, again due to using
    # StringIO
    if mirror_local_mode and mode is None:
        mode = os.stat(filename).st_mode
        # To prevent put() from trying to do this
        # logic itself
        mirror_local_mode = False

    # Process template
    text = render_template(filename, context=context,
                           use_jinja=use_jinja,
                           template_dir=template_dir)

    # Back up original file
    if backup and exists(destination):
        func("cp %s{,.bak}" % destination)

    # Upload the file.
    put(
        local_path=StringIO(text),
        remote_path=destination,
        use_sudo=use_sudo,
        mirror_local_mode=mirror_local_mode,
        mode=mode
    )


def upload_first(filenames, destination, *args, **kwargs):
    for filename in filenames:
        try:
            upload_template(filename, destination, *args, **kwargs)
        except DeployTemplateNotFound, err:
            if err.name != filename:
                raise
            continue
        else:
            return
    raise DeployTemplateNotFound(filename)
