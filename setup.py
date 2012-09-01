# -*- coding: utf-8 -
#
# This file is part of speedydeploy released under the MIT license. 
# See the NOTICE for more information.

import os
from setuptools import setup, find_packages
import sys

from speedydeploy import get_version


setup(
    name='speedydeploy',
    version=get_version(),

    description='Speed deploy',
    long_description=file(
        os.path.join(
            os.path.dirname(__file__),
            'README.md'
        )
    ).read(),
    author='Victor Safronovich',
    author_email='vsafronovich@gmail.com',
    license='MIT',
    url='http://github.com/suvit/speedydeploy',

    classifiers=[
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
    zip_safe=False,
    packages=find_packages(exclude=['docs', 'examples', 'tests']),
    install_requires=file(
        os.path.join(
            os.path.dirname(__file__),
            'speedydeploy',
            'requirements.txt'
        )
    ).read().split(),
    include_package_data=True,
)
