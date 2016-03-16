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
>>> ext_cli = FlaskCLI(app)

There are several dependencies that should be initialized in order to make
OAIServer work correctly.

>>> from invenio_db import InvenioDB
>>> from invenio_indexer import InvenioIndexer
>>> from invenio_pidstore import InvenioPIDStore
>>> from invenio_records import InvenioRecords
>>> from invenio_search import InvenioSearch
>>> ext_db = InvenioDB(app)
>>> ext_indexer = InvenioIndexer(app)
>>> ext_pidstore = InvenioPIDStore(app)
>>> ext_records = InvenioRecords(app)
>>> ext_search = InvenioSearch(app)

Then you can initialize OAIServer like a normal Flask extension, however
you need to set following configuration options first:

>>> app.config['OAISERVER_RECORD_INDEX'] = 'records-record-v1.0.0',
>>> app.config['OAISERVER_ID_PREFIX'] = 'oai:localhost:recid/',
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
"""

from __future__ import absolute_import, print_function

from .ext import InvenioOAIServer
from .proxies import current_oaiserver
from .version import __version__

__all__ = ('__version__', 'InvenioOAIServer', 'current_oaiserver')
