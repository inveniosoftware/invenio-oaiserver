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

r"""Minimal Flask application example for development.

Create database and tables:

.. code-block:: console

    $ cd examples
    $ flask -a app.py db init
    $ flask -a app.py db create

Load demo records from invenio-records (see
invenio_records/data/marc21/bibliographic.xml):

.. code-block:: console

    $ dojson -i data/marc21/bibliographic.xml -l marcxml do marc21 | \
        flask -a app.py records create

Mint the records:

.. code-block:: console

    $ flask -a app.py fixtures oaiserver

"""

from __future__ import absolute_import, print_function

import os
import uuid

import click
from flask import Flask
from flask_cli import FlaskCLI
from invenio_db import InvenioDB
from invenio_indexer import InvenioIndexer
from invenio_indexer.api import RecordIndexer
from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.minters import recid_minter
from invenio_records import InvenioRecords
from invenio_search import InvenioSearch

from invenio_oaiserver import InvenioOAIServer
from invenio_oaiserver.minters import oaiid_minter

# Create Flask application
app = Flask(__name__)
app.config.update(
    OAISERVER_RECORD_INDEX='records-record-v1.0.0',
    OAISERVER_ID_PREFIX='oai:localhost:recid/',
    SECRET_KEY='CHANGE_ME',
    SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                      'sqlite:///app.db'),
)
FlaskCLI(app)
InvenioDB(app)
InvenioRecords(app)
InvenioPIDStore(app)
search = InvenioSearch(app)
InvenioIndexer(app)
InvenioOAIServer(app)


@app.cli.group()
def fixtures():
    """Initialize example data."""


@fixtures.command()
@click.option('-s', 'sets', type=click.INT, default=27)
@click.option('-r', 'records', type=click.INT, default=27)
def oaiserver(sets, records):
    """Initialize OAI-PMH server."""
    from invenio_db import db
    from invenio_oaiserver.models import OAISet
    from invenio_records.api import Record

    # create a OAI Set
    with db.session.begin_nested():
        for i in range(sets):
            db.session.add(OAISet(
                spec='test{0}'.format(i),
                name='Test{0}'.format(i),
                description='test desc {0}'.format(i),
                search_pattern='title:Test{0}'.format(i),
            ))

    # create a record
    schema = {
        'type': 'object',
        'properties': {
            'title': {'type': 'string'},
            'field': {'type': 'boolean'},
        },
        'required': ['title'],
    }

    search.client.indices.delete_alias('_all', '_all', ignore=[400, 404])
    search.client.indices.delete('*')

    with app.app_context():
        indexer = RecordIndexer()
        with db.session.begin_nested():
            for i in range(records):
                record_id = uuid.uuid4()
                data = {'title': 'Test{0}'.format(i), '$schema': schema}
                recid_minter(record_id, data)
                oaiid_minter(record_id, data)
                record = Record.create(data, id_=record_id)
                indexer.index(record)

        db.session.commit()
