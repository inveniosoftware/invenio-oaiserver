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

"""Invenio module that implements OAI-PMH server.

Invenio-OAIServer is exposing records via OAI-PMH protocol. The core part
is reponsible for managing OAI sets that are defined using queries.

OAIServer consists of:

- OAI-PMH 2.0 compatible endpoint.
- Persistent identifier minters, fetchers and providers.
- Backend for formating Elastic search results.

Initialization
--------------
First create a Flask application (Flask-CLI is not needed for Flask
version 1.0+):

>>> from flask import Flask
>>> from flask_cli import FlaskCLI
>>> app = Flask('myapp')
>>> app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
>>> app.config['CELERY_ALWAYS_EAGER'] = True
>>> ext_cli = FlaskCLI(app)

There are several dependencies that should be initialized in order to make
OAIServer work correctly.

>>> from invenio_db import InvenioDB
>>> from invenio_indexer import InvenioIndexer
>>> from invenio_pidstore import InvenioPIDStore
>>> from invenio_records import InvenioRecords
>>> from invenio_search import InvenioSearch
>>> from flask_celeryext import FlaskCeleryExt
>>> ext_db = InvenioDB(app)
>>> ext_indexer = InvenioIndexer(app)
>>> ext_pidstore = InvenioPIDStore(app)
>>> ext_records = InvenioRecords(app)
>>> ext_search = InvenioSearch(app)
>>> ext_celery = FlaskCeleryExt(app)

Then you can initialize OAIServer like a normal Flask extension, however
you need to set following configuration options first:

>>> app.config['OAISERVER_RECORD_INDEX'] = 'marc21',
>>> app.config['OAISERVER_ID_PREFIX'] = 'oai:example:',
>>> from invenio_oaiserver import InvenioOAIServer
>>> ext_oaiserver = InvenioOAIServer(app)

In order for the following examples to work, you need to work within an
Flask application context so let's push one:

>>> ctx = app.app_context()
>>> ctx.push()

Also, for the examples to work we need to create the database and tables (note,
in this example we use an in-memory SQLite database):

>>> from invenio_db import db
>>> db.create_all()

And create the indices on Elasticsearch.

>>> indices = list(ext_search.create(ignore=[400]))
>>> from time import sleep
>>> sleep(5)

Creating OAI sets
-----------------
"A set is an optional construct for grouping records for the purpose of
selective harvesting" [OAISet]_. The easiest way to create new OAI set is
using database model.

>>> from invenio_oaiserver.models import OAISet
>>> oaiset = OAISet(spec='higgs', name='Higgs', description='...')
>>> oaiset.search_pattern = 'title:higgs'
>>> db.session.add(oaiset)
>>> db.session.commit()

The above set will group all records that contain word "higgs" in the title.

We can now see the set by using verb ``ListSets``:

>>> with app.test_client() as client:
...     res = client.get('/oai2d?verb=ListSets')
>>> res.status_code
200
>>> b'Higgs' in res.data
True

.. [OAISet] https://www.openarchives.org/OAI/openarchivesprotocol.html#Set

Data model
----------
Response serializer, indexer and search expect ``_oai`` key in record data
with following structure.

.. code-block:: text

    {
        "_oai": {
            "id": "oai:example:1",
            "sets": ["higgs", "demo"],
            "updated": "2012-07-04T15:00:00Z"
        }
    }

There **must** exist a ``id`` key with not null value otherwise the record
is not exposed via OAI-PHM interface (``listIdentifiers``, ``listRecords``).
The value of this field should be regitered in PID store. We provide default
:func:`~invenio_oaiserver.minters.oaiid_minter` that can register existing
value or mint new one by concatenating a configuration option
``OAISERVER_ID_PREFIX`` and record value from ``control_number`` field.

All values in ``sets`` must exist in ``spec`` column in ``oaiserver_set``
table or they will be removed when record updater is executed. The last
field ``updated`` contains ISO8601 datetime of the last record metadata
modification acording to following rules for `selective harvesting`_.

.. _selective harvesting: https://www.openarchives.org/OAI/openarchivesprotocol.html#SelectiveHarvestingandDatestamps
"""

from __future__ import absolute_import, print_function

from .ext import InvenioOAIServer
from .proxies import current_oaiserver
from .version import __version__

__all__ = ('__version__', 'InvenioOAIServer', 'current_oaiserver')
