# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Invenio module that implements OAI-PMH server."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'check-manifest>=0.25',
    'coverage>=4.0',
    'invenio-marc21>=1.0.0a2',
    'isort>=4.2.2',
    'mock>=1.3.0',
    'pydocstyle>=1.0.0',
    'pytest-cache>=1.0',
    'pytest-cov>=1.8.0',
    'pytest-pep8>=1.0.6',
    'pytest>=2.8.0',
]

extras_require = {
    ':python_version=="2.7"': [
        'functools32>=3.2.3',
    ],
    'admin': [
        'Flask-Admin>=1.3.0',
    ],
    'docs': [
        'Sphinx>=1.3',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    if name[0] == ':':
        continue
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=2.6.2',
]

install_requires = [
    'Flask-BabelEx>=0.9.2',
    'dojson>=1.2.0',
    'elasticsearch-dsl>=2.0.0',
    'invenio-db>=1.0.0a9',
    'invenio-indexer>=1.0.0a2',
    'invenio-pidstore>=1.0.0a7',
    'invenio-query-parser>=0.6.0',
    'invenio-records>=1.0.0a14',
    'invenio-search>=1.0.0a7',
    'lxml>=3.5.0',
    'marshmallow>=2.5.0',
    'webargs>=1.1.0',
]

packages = find_packages()

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_oaiserver', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-oaiserver',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio OAI-PMH',
    license='GPLv2',
    author='CERN',
    author_email='info@invenio-software.org',
    url='https://github.com/inveniosoftware/invenio-oaiserver',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_base.apps': [
            'invenio_oaiserver = invenio_oaiserver:InvenioOAIServer',
        ],
        'invenio_db.models': [
            'invenio_oaiserver = invenio_oaiserver.models',
        ],
        'invenio_admin.views': [
            'invenio_oaiserver = invenio_oaiserver.admin:set_adminview',
        ],
        'invenio_pidstore.minters': [
            'oaiid = invenio_oaiserver.minters:oaiid_minter',
        ],
        'invenio_pidstore.fetchers': [
            'oaiid = invenio_oaiserver.fetchers:oaiid_fetcher',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 1 - Planning',
    ],
)
