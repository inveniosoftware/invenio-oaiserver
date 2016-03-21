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

"""Test record listing."""

from __future__ import absolute_import

import pytest
from flask import url_for
from lxml import etree

from invenio_oaiserver.response import NS_DC, NS_OAIDC, NS_OAIPMH

NAMESPACES = {'x': NS_OAIPMH, 'y': NS_OAIDC, 'z': NS_DC}


@pytest.mark.parametrize('metadata_prefix', ['oai_dc', 'marcxml'])
def test_list_all_records(app, bibliographic_data, metadata_prefix):
    """Test ListRecords."""
    kwargs = dict(verb='ListRecords', metadataPrefix=metadata_prefix)

    pages = len(bibliographic_data)//10
    for page in range(pages+1):
        with app.app_context():
            with app.test_client() as c:
                result = c.get(url_for('invenio_oaiserver.response', **kwargs))

        tree = etree.fromstring(result.data)

        assert len(tree.xpath('/x:OAI-PMH', namespaces=NAMESPACES)) == 1
        assert len(tree.xpath('/x:OAI-PMH/x:ListRecords',
                              namespaces=NAMESPACES)) == 1

        resumption_token = tree.xpath(
            '/x:OAI-PMH/x:ListRecords/x:resumptionToken', namespaces=NAMESPACES
        )[0]

        if resumption_token.text:
            kwargs['resumptionToken'] = resumption_token.text
            kwargs.pop('metadataPrefix', None)

            assert len(tree.xpath('/x:OAI-PMH/x:ListRecords/x:record',
                                  namespaces=NAMESPACES)) == 10
        else:  # last page has just 6 records
            assert pages == page
            num_records = len(tree.xpath('/x:OAI-PMH/x:ListRecords/x:record',
                                         namespaces=NAMESPACES))
            assert len(bibliographic_data) % 10 == num_records
