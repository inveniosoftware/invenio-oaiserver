# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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

import pkg_resources
import pytest
from elasticsearch import Elasticsearch
from flask import Flask
from flask_cli import FlaskCLI
from invenio_db import InvenioDB, db
from invenio_indexer import InvenioIndexer
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_search import InvenioSearch

from invenio_oaiserver import InvenioOAIServer


def dump_etree(record, **kwargs):
    """Test dumper."""
    from dojson.contrib.to_marc21.utils import dumps_etree
    return dumps_etree({'245__': {'a': record['title']}}, **kwargs)


@pytest.fixture()
def app(request):
    """Flask application fixture."""
    instance_path = tempfile.mkdtemp()
    app = Flask('testapp', instance_path=instance_path)
    app.config.update(
        TESTING=True,
        SECRET_KEY='CHANGE_ME',
        SQLALCHEMY_DATABASE_URI=os.environ.get('SQLALCHEMY_DATABASE_URI',
                                               'sqlite://'),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SERVER_NAME='app',
        OAISERVER_RECORD_INDEX='records-record-v1.0.0',
        OAISERVER_METADATA_FORMATS={
            'oai_dc': {
                'serializer': (
                    'conftest:dump_etree',
                    {
                        'xslt_filename': pkg_resources.resource_filename(
                            'invenio_oaiserver', 'static/xsl/oai2.v1.0.xsl')
                    }
                ),
                'schema': 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
                'namespace': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
            }
        },
    )
    FlaskCLI(app)
    InvenioDB(app)
    InvenioRecords(app)
    InvenioPIDStore(app)
    client = Elasticsearch(hosts=[os.environ.get('ES_HOST', 'localhost')])
    search = InvenioSearch(app, client=client)
    search.register_mappings('records', 'data')
    InvenioIndexer(app)
    InvenioOAIServer(app)

    with app.app_context():
        db.create_all()
        list(search.create(ignore=[400]))

    def teardown():
        with app.app_context():
            list(search.delete(ignore=[404]))
            db.drop_all()
        shutil.rmtree(instance_path)

    request.addfinalizer(teardown)
    return app
