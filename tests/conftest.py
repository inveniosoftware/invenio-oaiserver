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


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os
import shutil
import tempfile
from time import sleep

import pytest
from elasticsearch import Elasticsearch
from flask import Flask
from flask_celeryext import FlaskCeleryExt
from flask_cli import FlaskCLI
from helpers import load_records, remove_records
from invenio_db import InvenioDB, db
from invenio_indexer import InvenioIndexer
from invenio_marc21 import InvenioMARC21
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_search import InvenioSearch

from invenio_oaiserver import InvenioOAIServer


@pytest.fixture()
def app(request):
    """Flask application fixture."""
    instance_path = tempfile.mkdtemp()
    app = Flask('testapp', instance_path=instance_path)
    app.config.update(
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND='memory',
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND='cache',
        TESTING=True,
        SECRET_KEY='CHANGE_ME',
        SQLALCHEMY_DATABASE_URI=os.environ.get('SQLALCHEMY_DATABASE_URI',
                                               'sqlite://'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SERVER_NAME='app',
        OAISERVER_RECORD_INDEX='_all',
        # Disable set signals because the celery tasks cannot be run
        # synchronously
        OAISERVER_REGISTER_SET_SIGNALS=False,
        SEARCH_ELASTIC_KEYWORD_MAPPING={None: ['_all']},
    )

    FlaskCLI(app)
    InvenioDB(app)
    FlaskCeleryExt(app)
    InvenioRecords(app)
    InvenioPIDStore(app)
    InvenioMARC21(app)
    client = Elasticsearch(hosts=[os.environ.get('ES_HOST', 'localhost')])
    search = InvenioSearch(app, client=client)
    search.register_mappings('records', 'data')
    InvenioIndexer(app)
    InvenioOAIServer(app)

    with app.app_context():
        db.create_all()
        list(search.create(ignore=[400]))
        sleep(5)

    def teardown():
        with app.app_context():
            list(search.delete(ignore=[404]))
            db.drop_all()
        shutil.rmtree(instance_path)

    request.addfinalizer(teardown)
    return app


def mock_record_validate(self):
    """Mock validation."""
    pass


@pytest.yield_fixture
def authority_data(app):
    """Test indexation using authority data."""
    schema = 'http://localhost:5000/marc21/authority/ad-v1.0.0.json'
    with app.test_request_context():
        records = load_records(app=app, filename='data/marc21/authority.xml',
                               schema=schema)
    yield records
    with app.test_request_context():
        remove_records(app, records)


@pytest.yield_fixture
def bibliographic_data(app):
    """Test indexation using bibliographic data."""
    schema = 'http://localhost:5000/marc21/bibliographic/bd-v1.0.0.json'
    with app.test_request_context():
        records = load_records(app=app,
                               filename='data/marc21/bibliographic.xml',
                               schema=schema)
    yield records
    with app.test_request_context():
        remove_records(app, records)
