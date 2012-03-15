# -*- coding: utf-8 -
#
# This file is part of speedydeploy released under the MIT license. 
# See the NOTICE for more information.

import os
from setuptools import setup, find_packages
import sys

from speedydeploy import __version__


setup(
    name = 'speedydeploy',
    version = __version__,

    description = 'Speed deploy',
    long_description = 'Speed deploy',
    author = 'Victor Safronovich',
    author_email = 'vsafronovich@gmail.com',
    license = 'MIT',
    url = 'http://github.com/suvit/speedydeploy',

    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Internet',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    zip_safe = False,
    packages = find_packages(exclude=['docs', 'examples', 'tests']),
    include_package_data = True,
)
