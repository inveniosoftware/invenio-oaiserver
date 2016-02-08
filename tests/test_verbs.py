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

"""Test OAI verbs."""

from __future__ import absolute_import

import uuid
from copy import deepcopy
from time import sleep

from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.minters import recid_minter
from invenio_records.api import Record
from lxml import etree

from invenio_oaiserver.minters import oaiid_minter
from invenio_oaiserver.models import OAISet
from invenio_oaiserver.response import NS_DC, NS_OAIDC, NS_OAIPMH, \
    datetime_to_datestamp


def _xpath_errors(body):
    """Find errors in body."""
    return list(body.iter('{*}error'))


def test_no_verb(app):
    """Test response when no verb is specified."""
    with app.test_client() as c:
        result = c.get('/oai2d')
        tree = etree.fromstring(result.data)
        assert 'Missing data for required field.' in _xpath_errors(
            tree)[0].text


def test_wrong_verb(app):
    with app.test_client() as c:
        result = c.get('/oai2d?verb=Aaa')
        tree = etree.fromstring(result.data)

        assert 'This is not a valid OAI-PMH verb:Aaa' in _xpath_errors(
            tree)[0].text


def test_identify(app):
    with app.test_client() as c:
        result = c.get('/oai2d?verb=Identify')
        assert 200 == result.status_code

        tree = etree.fromstring(result.data)

        namespaces = {'x': NS_OAIPMH}
        assert len(tree.xpath('/x:OAI-PMH', namespaces=namespaces)) == 1
        assert len(tree.xpath('/x:OAI-PMH/x:Identify',
                              namespaces=namespaces)) == 1
        repository_name = tree.xpath('/x:OAI-PMH/x:Identify/x:repositoryName',
                                     namespaces=namespaces)
        assert len(repository_name) == 1
        assert repository_name[0].text == 'Invenio-OAIServer'
        base_url = tree.xpath('/x:OAI-PMH/x:Identify/x:baseURL',
                              namespaces=namespaces)
        assert len(base_url) == 1
        assert base_url[0].text == 'http://app/oai2d'
        protocolVersion = tree.xpath('/x:OAI-PMH/x:Identify/x:protocolVersion',
                                     namespaces=namespaces)
        assert len(protocolVersion) == 1
        assert protocolVersion[0].text == '2.0'
        adminEmail = tree.xpath('/x:OAI-PMH/x:Identify/x:adminEmail',
                                namespaces=namespaces)
        assert len(adminEmail) == 1
        assert adminEmail[0].text == 'info@invenio-software.org'
        earliestDatestamp = tree.xpath(
            '/x:OAI-PMH/x:Identify/x:earliestDatestamp',
            namespaces=namespaces)
        assert len(earliestDatestamp) == 1
        deletedRecord = tree.xpath('/x:OAI-PMH/x:Identify/x:deletedRecord',
                                   namespaces=namespaces)
        assert len(deletedRecord) == 1
        assert deletedRecord[0].text == 'no'
        granularity = tree.xpath('/x:OAI-PMH/x:Identify/x:granularity',
                                 namespaces=namespaces)
        assert len(granularity) == 1


def test_getrecord(app):
    schema = {
        'type': 'object',
        'properties': {
            'title': {'type': 'string'},
            'field': {'type': 'boolean'},
        },
        'required': ['title'],
    }
    with app.test_request_context():
        with db.session.begin_nested():
            record = Record.create({'title': 'Test0', '$schema': schema}).model
            recid_minter(record.id, record.json)
            pid = oaiid_minter(record.id, record.json)

        db.session.commit()

        pid_value = pid.pid_value
        pid_updated = pid.updated

        with app.test_client() as c:
            result = c.get(
                "/oai2d?verb=GetRecord&identifier={0}&metadataPrefix=oai_dc"
                .format(pid_value))
            assert 200 == result.status_code

            tree = etree.fromstring(result.data)

            namespaces = {'x': NS_OAIPMH}
            assert len(tree.xpath('/x:OAI-PMH', namespaces=namespaces)) == 1
            assert len(tree.xpath('/x:OAI-PMH/x:GetRecord',
                                  namespaces=namespaces)) == 1
            assert len(tree.xpath('/x:OAI-PMH/x:GetRecord/x:header',
                                  namespaces=namespaces)) == 1
            assert len(tree.xpath(
                '/x:OAI-PMH/x:GetRecord/x:header/x:identifier',
                namespaces=namespaces)) == 1
            identifier = tree.xpath(
                '/x:OAI-PMH/x:GetRecord/x:header/x:identifier/text()',
                namespaces=namespaces)
            assert identifier == [str(record.id)]
            datestamp = tree.xpath(
                '/x:OAI-PMH/x:GetRecord/x:header/x:datestamp/text()',
                namespaces=namespaces)
            assert datestamp == [datetime_to_datestamp(pid_updated)]
            assert len(tree.xpath('/x:OAI-PMH/x:GetRecord/x:metadata',
                                  namespaces=namespaces)) == 1


def test_getrecord_fail(app):
    """Test GetRecord if record doesn't exist."""
    with app.test_request_context():
        with app.test_client() as c:
            result = c.get(
                "/oai2d?verb=GetRecord&identifier={0}&metadataPrefix=oai_dc"
                .format('not-exist-pid'))
            assert 422 == result.status_code

            tree = etree.fromstring(result.data)

            _check_xml_error(tree, code='idDoesNotExist')


def _check_xml_error(tree, code):
    """Text xml for a error idDoesNotExist."""
    namespaces = {'x': NS_OAIPMH}
    assert len(tree.xpath('/x:OAI-PMH', namespaces=namespaces)) == 1
    error = tree.xpath('/x:OAI-PMH/x:error', namespaces=namespaces)
    assert len(error) == 1
    assert error[0].attrib['code'] == code


def test_identify_with_additional_args(app):
    with app.test_client() as c:
        result = c.get('/oai2d?verb=Identify&notAValidArg=True')
        tree = etree.fromstring(result.data)
        assert 'You have passed too many arguments.' == _xpath_errors(
            tree)[0].text


def test_listmetadataformats(app):
    """Test ListMetadataFormats."""
    _listmetadataformats(app=app, query='/oai2d?verb=ListMetadataFormats')


def test_listmetadataformats_record(app):
    """Test ListMetadataFormats for a record."""
    schema = {
        'type': 'object',
        'properties': {
            'title': {'type': 'string'},
            'field': {'type': 'boolean'},
        },
        'required': ['title'],
    }
    with app.test_request_context():
        with db.session.begin_nested():
            record_id = uuid.uuid4()
            data = {'title': 'Test0', '$schema': schema}
            recid_minter(record_id, data)
            pid = oaiid_minter(record_id, data)
            Record.create(data, id_=record_id)
            pid_value = pid.pid_value

        db.session.commit()

    _listmetadataformats(
        app=app,
        query='/oai2d?verb=ListMetadataFormats&identifier={0}'.format(
            pid_value))


def test_listmetadataformats_record_fail(app):
    """Test ListMetadataFormats for a record that doesn't exist."""
    query = '/oai2d?verb=ListMetadataFormats&identifier={0}'.format(
            "pid-not-exixts")
    with app.test_request_context():
        with app.test_client() as c:
            result = c.get(query)

        tree = etree.fromstring(result.data)

        _check_xml_error(tree, code='idDoesNotExist')


def _listmetadataformats(app, query):
    """Try ListMetadataFormats."""
    with app.test_request_context():
        with app.test_client() as c:
            result = c.get(query)

        tree = etree.fromstring(result.data)

        namespaces = {'x': NS_OAIPMH}
        assert len(tree.xpath('/x:OAI-PMH', namespaces=namespaces)) == 1
        assert len(tree.xpath('/x:OAI-PMH/x:ListMetadataFormats',
                              namespaces=namespaces)) == 1
        metadataFormats = tree.xpath(
            '/x:OAI-PMH/x:ListMetadataFormats/x:metadataFormat',
            namespaces=namespaces)
        cfg_metadataFormats = deepcopy(
            app.config.get('OAISERVER_METADATA_FORMATS', {}))
        assert len(metadataFormats) == len(cfg_metadataFormats)
        for metadataFormat in metadataFormats:
            # prefix
            prefix = metadataFormat.xpath(
                '/x:OAI-PMH/x:ListMetadataFormats/x:metadataFormat/'
                'x:metadataPrefix', namespaces=namespaces)
            assert len(prefix) == 1
            assert prefix[0].text in cfg_metadataFormats
            # schema
            schema = metadataFormat.xpath(
                '/x:OAI-PMH/x:ListMetadataFormats/x:metadataFormat/'
                'x:schema', namespaces=namespaces)
            assert len(schema) == 1
            assert schema[0].text in cfg_metadataFormats[
                prefix[0].text]['schema']
            # metadataNamespace
            metadataNamespace = metadataFormat.xpath(
                '/x:OAI-PMH/x:ListMetadataFormats/x:metadataFormat/'
                'x:metadataNamespace', namespaces=namespaces)
            assert len(metadataNamespace) == 1
            assert metadataNamespace[0].text in cfg_metadataFormats[
                prefix[0].text]['namespace']
            # remove tested format
            del cfg_metadataFormats[prefix[0].text]


def test_listsets(app):
    """Test ListSets."""
    with app.test_request_context():
        with db.session.begin_nested():
            a = OAISet(spec='test', name='Test', description="test desc")
            db.session.add(a)

        with app.test_client() as c:
            result = c.get('/oai2d?verb=ListSets')

        tree = etree.fromstring(result.data)

        namespaces = {'x': NS_OAIPMH}
        assert len(tree.xpath('/x:OAI-PMH', namespaces=namespaces)) == 1

        assert len(tree.xpath('/x:OAI-PMH/x:ListSets',
                              namespaces=namespaces)) == 1
        assert len(tree.xpath('/x:OAI-PMH/x:ListSets/x:set',
                              namespaces=namespaces)) == 1
        assert len(tree.xpath('/x:OAI-PMH/x:ListSets/x:set/x:setSpec',
                              namespaces=namespaces)) == 1
        assert len(tree.xpath('/x:OAI-PMH/x:ListSets/x:set/x:setName',
                              namespaces=namespaces)) == 1
        assert len(tree.xpath(
            '/x:OAI-PMH/x:ListSets/x:set/x:setDescription',
            namespaces=namespaces
        )) == 1
        namespaces['y'] = NS_OAIDC
        assert len(
            tree.xpath('/x:OAI-PMH/x:ListSets/x:set/x:setDescription/y:dc',
                       namespaces=namespaces)
        ) == 1
        namespaces['z'] = NS_DC
        assert len(
            tree.xpath('/x:OAI-PMH/x:ListSets/x:set/x:setDescription/y:dc/'
                       'z:description', namespaces=namespaces)
        ) == 1
        text = tree.xpath(
            '/x:OAI-PMH/x:ListSets/x:set/x:setDescription/y:dc/'
            'z:description/text()', namespaces=namespaces)
        assert len(text) == 1
        assert text[0] == 'test desc'


def test_fail_missing_metadataPrefix(app):
    """Test ListRecords fail missing metadataPrefix."""
    queries = [
        '/oai2d?verb=ListRecords',
        '/oai2d?verb=GetRecord&identifier=123',
        '/oai2d?verb=ListIdentifiers'
    ]
    for query in queries:
        with app.test_request_context():
            with app.test_client() as c:
                result = c.get(query)

            tree = etree.fromstring(result.data)

            _check_xml_error(tree, code='badArgument')


def test_fail_not_exist_metadataPrefix(app):
    """Test ListRecords fail not exist metadataPrefix."""
    queries = [
        '/oai2d?verb=ListRecords&metadataPrefix=not-exist',
        '/oai2d?verb=GetRecord&identifier=123&metadataPrefix=not-exist',
        '/oai2d?verb=ListIdentifiers&metadataPrefix=not-exist'
    ]
    for query in queries:
        with app.test_request_context():
            with app.test_client() as c:
                result = c.get(query)

            tree = etree.fromstring(result.data)

            _check_xml_error(tree, code='badArgument')


def test_listrecords_fail_missing_metadataPrefix(app):
    """Test ListRecords fail missing metadataPrefix."""
    query = '/oai2d?verb=ListRecords&'
    with app.test_request_context():
        with app.test_client() as c:
            result = c.get(query)

        tree = etree.fromstring(result.data)

        _check_xml_error(tree, code='badArgument')


def test_listrecords(app):
    """Test ListRecords."""
    schema = {
        'type': 'object',
        'properties': {
            'title': {'type': 'string'},
            'field': {'type': 'boolean'},
        },
        'required': ['title'],
    }
    with app.test_request_context():
        indexer = RecordIndexer()

        with db.session.begin_nested():
            record_id = uuid.uuid4()
            data = {'title': 'Test0', '$schema': schema}
            recid_minter(record_id, data)
            oaiid_minter(record_id, data)
            record = Record.create(data, id_=record_id)

        db.session.commit()

        indexer.index_by_id(record_id)
        sleep(1)

        with app.test_client() as c:
            result = c.get('/oai2d?verb=ListRecords&metadataPrefix=oai_dc')

        tree = etree.fromstring(result.data)

        namespaces = {'x': NS_OAIPMH}
        assert len(tree.xpath('/x:OAI-PMH', namespaces=namespaces)) == 1

        assert len(tree.xpath('/x:OAI-PMH/x:ListRecords',
                              namespaces=namespaces)) == 1
        assert len(tree.xpath('/x:OAI-PMH/x:ListRecords/x:record',
                              namespaces=namespaces)) == 1
        assert len(tree.xpath('/x:OAI-PMH/x:ListRecords/x:record/x:header',
                              namespaces=namespaces)) == 1
        assert len(tree.xpath('/x:OAI-PMH/x:ListRecords/x:record/x:header'
                              '/x:identifier', namespaces=namespaces)) == 1
        assert len(tree.xpath('/x:OAI-PMH/x:ListRecords/x:record/x:header'
                              '/x:datestamp', namespaces=namespaces)) == 1
        assert len(tree.xpath('/x:OAI-PMH/x:ListRecords/x:record/x:metadata',
                              namespaces=namespaces)) == 1


def test_listidentifiers(app):
    """Test verb ListIdentifiers."""
    schema = {
        'type': 'object',
        'properties': {
            'title': {'type': 'string'},
            'field': {'type': 'boolean'},
        },
        'required': ['title'],
    }
    with app.test_request_context():
        indexer = RecordIndexer()

        with db.session.begin_nested():
            record_id = uuid.uuid4()
            data = {'title': 'Test0', '$schema': schema}
            recid_minter(record_id, data)
            pid = oaiid_minter(record_id, data)
            record = Record.create(data, id_=record_id)

        db.session.commit()

        indexer.index_by_id(record_id)
        sleep(1)

        pid_value = pid.pid_value

        with app.test_client() as c:
            result = c.get(
                "/oai2d?verb=ListIdentifiers&metadataPrefix=oai_dc"
            )

        tree = etree.fromstring(result.data)

        namespaces = {'x': NS_OAIPMH}
        assert len(tree.xpath('/x:OAI-PMH', namespaces=namespaces)) == 1
        assert len(tree.xpath('/x:OAI-PMH/x:ListIdentifiers',
                              namespaces=namespaces)) == 1
        assert len(tree.xpath('/x:OAI-PMH/x:ListIdentifiers/x:header',
                              namespaces=namespaces)) == 1
        identifier = tree.xpath(
            '/x:OAI-PMH/x:ListIdentifiers/x:header/x:identifier',
            namespaces=namespaces
        )
        assert len(identifier) == 1
        assert identifier[0].text == str(pid_value)
        datestamp = tree.xpath(
            '/x:OAI-PMH/x:ListIdentifiers/x:header/x:datestamp',
            namespaces=namespaces
        )
        assert len(datestamp) == 1
        assert datestamp[0].text == datetime_to_datestamp(record.updated)


def test_list_sets_long(app):
    with app.test_client() as c:
        result = c.get('/oai2d?verb=ListSets')


def test_list_sets_with_resumption_token(app):
    pass


def test_list_sets_with_second_resumption_token(app):
    pass


def test_list_sets_with_resumption_token_and_other_args(app):
    pass
