# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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


"""Test CLI."""

from __future__ import absolute_import, print_function

import uuid

from datetime import datetime
from time import sleep

from click.testing import CliRunner
from dateutil.parser import parse as iso2dt
from flask.cli import ScriptInfo
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.minters import recid_minter
from invenio_records.api import Record

from invenio_oaiserver.cli import oaipmh as cmd
from invenio_oaiserver.minters import oaiid_minter
from invenio_oaiserver.models import OAISet
from invenio_oaiserver.proxies import current_oaiserver


def test_simple_workflow(app):
    """Run simple workflow."""
    indexer = RecordIndexer()
    runner = CliRunner()
    script_info = ScriptInfo(create_app=lambda info: app)

    with app.app_context():
        record_id = uuid.uuid4()
        item_dict = {'title': 'Test1'}
        recid_minter(record_id, item_dict)
        oaiid_minter(record_id, item_dict)
        record = Record.create(item_dict, id_=record_id)
        oaiset1 = OAISet(spec='abc', search_pattern='title:"Test1"')
        db.session.add(oaiset1)
        db.session.commit()
        assert not record['_oai'].get('sets', [])

        # Keep identifiers
        record_id = record.id
        oaiset1_id = oaiset1.id

        indexer.index(record)
        sleep(10)

    result = runner.invoke(cmd, [
        'update', '--search-pattern', 'title:"Test1"', '--yes-i-know'
    ], obj=script_info)
    assert 0 == result.exit_code

    with app.app_context():
        record = Record.get_record(record_id)
        assert 'abc' in record['_oai']['sets']
        assert 'updated' in record['_oai']
        dt1 = iso2dt(record['_oai']['updated'])
        assert dt1.year == datetime.utcnow().year  # Test if parsed OK

        indexer.index(record)
        sleep(10)

        OAISet.query.filter_by(id=oaiset1.id).delete()
        db.session.commit()

    result = runner.invoke(cmd, [
        'update', '--spec', 'abc', '--yes-i-know'
    ], obj=script_info)
    assert 0 == result.exit_code

    with app.app_context():
        record = Record.get_record(record_id)
        assert 'abc' not in record['_oai']['sets']
        dt2 = iso2dt(record['_oai']['updated'])
        assert dt2 >= dt1
