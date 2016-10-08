# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
# -*- coding: utf-8 -*-
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""Percolator test cases."""

import uuid
from datetime import datetime
from time import sleep

import pytest
from dateutil.parser import parse as iso2dt
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.minters import recid_minter
from invenio_records.api import Record
from invenio_records.models import RecordMetadata
from mock import patch

from invenio_oaiserver import current_oaiserver
from invenio_oaiserver.errors import OAISetSpecUpdateError
from invenio_oaiserver.minters import oaiid_minter
from invenio_oaiserver.models import OAISet
from invenio_oaiserver.receivers import after_delete_oai_set, \
    after_insert_oai_set, after_update_oai_set


def test_populate_oaisets(app, with_record_signals):
    """Populate OAISets."""
    indexer = RecordIndexer()
    schema = {
        'allOf': [{
            'type': 'object',
            'properties': {
                'title': {'type': 'string'},
                'genre': {'type': 'string'},
                'field': {'type': 'boolean'},
            },
            'required': ['title'],
        }, {
            '$ref': 'http://inveniosoftware.org/schemas/'
                    'oaiserver/internal-v1.0.0.json',
        }]
    }

    def create_record(item_dict, mint_oaiid=True):
        """Create test record."""
        with app.test_request_context():
            record_id = uuid.uuid4()
            recid_minter(record_id, item_dict)
            if mint_oaiid:
                oaiid_minter(record_id, item_dict)
            record = Record.create(item_dict, id_=record_id)
            indexer.index(record)
            return record

    a = OAISet(spec='a')
    b = OAISet(spec='b')
    e = OAISet(
        spec="e", search_pattern="title:Test2 OR title:Test3")
    c = OAISet(spec="c", search_pattern="title:Test0")
    d = OAISet(spec="d", search_pattern="title:Test1")
    f = OAISet(spec="f", search_pattern="title:Test2")
    g = OAISet(spec="g")
    h = OAISet(spec="h")
    i = OAISet(spec="i", search_pattern="title:Test3")
    j = OAISet(spec="j with space", search_pattern="title:Test4")
    # Note below: brackets around AND search query are required
    l = OAISet(spec="math",
               search_pattern="(title:foo AND genre:math)")
    m = OAISet(spec="nonmath",
               search_pattern="(title:foo AND -genre:math)")

    with db.session.begin_nested():
        for oaiset in [a, b, c, d, e, f, g, h, i, j, l, m]:
            db.session.add(oaiset)

    db.session.commit()

    a_id = a.id
    i_id = i.id

    # start tests

    record0 = create_record({
        '_oai': {'sets': ['a']}, 'title': 'Test0', '$schema': schema
    })

    assert 'a' in record0['_oai']['sets'], 'Keep manually managed set "a".'
    assert 'c' in record0['_oai']['sets']
    assert len(record0['_oai']['sets']) == 2

    record_not_found = create_record(
        {'title': 'TestNotFound', '$schema': schema}
    )

    # Don't create empty sets list just because of commit
    assert 'sets' not in record_not_found['_oai']

    record1 = create_record({'title': 'Test1', '$schema': schema})

    assert 'd' in record1['_oai']['sets']
    assert len(record1['_oai']['sets']) == 1

    record2 = create_record({'title': 'Test2', '$schema': schema})
    record2_id = record2.id

    assert 'e' in record2['_oai']['sets']
    assert 'f' in record2['_oai']['sets']
    assert len(record2['_oai']['sets']) == 2

    record3 = create_record({'title': 'Test3', '$schema': schema})
    record3_id = record3.id

    assert 'e' in record3['_oai']['sets']
    assert 'i' in record3['_oai']['sets']
    assert len(record3['_oai']['sets']) == 2

    record4 = create_record({'title': 'Test4', '$schema': schema})
    record4_id = record4.id

    assert 'j with space' in record4['_oai']['sets']
    assert len(record4['_oai']['sets']) == 1

    # If record does not have '_oai', don't add any sets,
    # nor even the default '_oai' key
    record5 = create_record({'title': 'Test1', '$schema': schema},
                            mint_oaiid=False)
    assert '_oai' not in record5

    # If 'sets' before and after record commit are equivalent
    # don't bump up the '_oai.updated' timestamp...
    record6 = create_record({'title': 'Test1', '$schema': schema})
    assert record6['_oai']['sets'] == ['d']
    prev_updated_r6 = record6['_oai']['updated']
    record6.commit()
    assert record6['_oai']['sets'] == ['d']
    assert record6['_oai']['updated'] == prev_updated_r6  # date stays the same

    # ...but do bump up '_oai.updated' if the sets are different
    record7 = create_record({'title': 'Test1', '$schema': schema})
    assert record7['_oai']['sets'] == ['d']
    prev_updated_r7 = record7['_oai']['updated']
    sleep(1)  # 'updated' timestamp is accurate to a second, hence the wait
    record7['_oai']['sets'] = ['d', 'f']  # 'f' should be removed after commit
    record7.commit()
    assert record7['_oai']['sets'] == ['d']
    assert record7['_oai']['updated'] != prev_updated_r7  # date bumped

    # Test 'AND' keyword for records
    record8 = create_record(
        {'title': 'foo', 'genre': 'math', '$schema': schema})
    assert record8['_oai']['sets'] == ['math', ]

    record9 = create_record(
        {'title': 'foo', 'genre': 'physics', '$schema': schema})
    assert record9['_oai']['sets'] == ['nonmath', ]

    record10 = create_record(
        {'title': 'bar', 'genre': 'math', '$schema': schema})
    assert 'sets' not in record10['_oai']  # title is not 'foo'

    # wait ElasticSearch end to index records
    sleep(10)

    # test delete
    current_oaiserver.unregister_signals_oaiset()
    with patch('invenio_oaiserver.receivers.after_delete_oai_set') as f:
        current_oaiserver.register_signals_oaiset()

        with db.session.begin_nested():
            db.session.delete(j)
        db.session.commit()
        assert f.called
        after_delete_oai_set(None, None, j)
        record4_model = RecordMetadata.query.filter_by(
            id=record4_id).first().json

        assert 'j with space' not in record4_model['_oai']['sets']
        assert len(record4_model['_oai']['sets']) == 0

        current_oaiserver.unregister_signals_oaiset()

    # test update search_pattern
    with patch('invenio_oaiserver.receivers.after_update_oai_set') as f:
        current_oaiserver.register_signals_oaiset()
        with db.session.begin_nested():
            i.search_pattern = None
            assert current_oaiserver.sets is None, 'Cache should be empty.'
            db.session.merge(i)
        db.session.commit()
        assert f.called
        i = OAISet.query.get(i_id)
        after_update_oai_set(None, None, i)
        record3_model = RecordMetadata.query.filter_by(
            id=record3_id).first().json

        assert 'i' in record3['_oai']['sets'], 'Set "i" is manually managed.'
        assert 'e' in record3_model['_oai']['sets']
        assert len(record3_model['_oai']['sets']) == 2

        current_oaiserver.unregister_signals_oaiset()

    # test update search_pattern
    with patch('invenio_oaiserver.receivers.after_update_oai_set') as f:
        current_oaiserver.register_signals_oaiset()

        with db.session.begin_nested():
            i.search_pattern = 'title:Test3'
            db.session.merge(i)
        db.session.commit()
        assert f.called
        i = OAISet.query.get(i_id)
        after_update_oai_set(None, None, i)
        record3_model = RecordMetadata.query.filter_by(
            id=record3_id).first().json

        assert 'e' in record3_model['_oai']['sets']
        assert 'i' in record3_model['_oai']['sets']
        assert len(record3_model['_oai']['sets']) == 2

        current_oaiserver.unregister_signals_oaiset()

    # test update the spec
    with pytest.raises(OAISetSpecUpdateError) as exc_info:
        a = OAISet.query.get(a_id)
        a.spec = 'new-a'
    assert exc_info.type is OAISetSpecUpdateError

    # test create new set
    with patch('invenio_oaiserver.receivers.after_insert_oai_set') as f:
        current_oaiserver.register_signals_oaiset()

        with db.session.begin_nested():
            k = OAISet(spec="k", search_pattern="title:Test2")
            db.session.add(k)
        db.session.commit()
        assert f.called
        after_insert_oai_set(None, None, k)
        record2_model = RecordMetadata.query.filter_by(
            id=record2_id).first().json

        assert 'e' in record2_model['_oai']['sets']
        assert 'f' in record2_model['_oai']['sets']
        assert 'k' in record2_model['_oai']['sets']
        assert len(record2_model['_oai']['sets']) == 3

        current_oaiserver.register_signals_oaiset()


def test_oaiset_add_remove_record(app):
    """Test the API method for manual record adding."""
    with app.app_context():
        oaiset1 = OAISet(spec='abc')
        rec1 = Record.create({'title': 'Test1'})
        assert not oaiset1.has_record(rec1)
        oaiset1.add_record(rec1)
        assert 'abc' in rec1['_oai']['sets']
        assert 'updated' in rec1['_oai']
        assert oaiset1.has_record(rec1)
        dt1 = iso2dt(rec1['_oai']['updated'])
        assert dt1.year == datetime.utcnow().year  # Test if parsed OK

        oaiset1.remove_record(rec1)
        assert 'abc' not in rec1['_oai']['sets']
        assert not oaiset1.has_record(rec1)
        dt2 = iso2dt(rec1['_oai']['updated'])
        assert dt2 >= dt1
