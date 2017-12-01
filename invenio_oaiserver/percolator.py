# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
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

"""Percolator."""

from __future__ import absolute_import, print_function

from elasticsearch import VERSION as ES_VERSION
from invenio_indexer.api import RecordIndexer
from invenio_search import current_search, current_search_client

from .models import OAISet
from .proxies import current_oaiserver
from .query import query_string_parser

# ES5 percolator
PERCOLATOR_DOC_TYPE = '.percolator' if ES_VERSION[0] == 2 else 'percolators'
PERCOLATOR_MAPPING = {
    'properties': {'query': {'type': 'percolator'}}
}


def _new_percolator(spec, search_pattern):
    """Create new percolator associated with the new set."""
    if spec and search_pattern:
        query = query_string_parser(search_pattern=search_pattern).to_dict()
        for name in current_search.mappings.keys():
            # Create the percolator doc_type in the existing index if ES5
            if ES_VERSION[0] > 2:
                current_search_client.indices.put_mapping(
                    index=name, doc_type=PERCOLATOR_DOC_TYPE,
                    body=PERCOLATOR_MAPPING, ignore=[400, 404])
            current_search_client.index(
                index=name, doc_type=PERCOLATOR_DOC_TYPE,
                id='oaiset-{}'.format(spec),
                body={'query': query}
            )


def _delete_percolator(spec, search_pattern):
    """Delete percolator associated with the new oaiset.

    :param target: Collection where the percolator was attached.
    """
    if spec:
        for name in current_search.mappings.keys():
            if ES_VERSION[0] > 2:
                current_search_client.indices.put_mapping(
                    index=name, doc_type=PERCOLATOR_DOC_TYPE,
                    body=PERCOLATOR_MAPPING, ignore=[400, 404])
            current_search_client.delete(
                index=name, doc_type=PERCOLATOR_DOC_TYPE,
                id='oaiset-{}'.format(spec), ignore=[404]
            )


def _build_cache():
    """Build sets cache."""
    sets = current_oaiserver.sets
    if sets is None:
        # build sets cache
        sets = current_oaiserver.sets = [
            oaiset.spec for oaiset in OAISet.query.filter(
                OAISet.search_pattern.is_(None)).all()]
    return sets


def get_record_sets(record):
    """Find matching sets."""
    # get lists of sets with search_pattern equals to None but already in the
    # set list inside the record
    record_sets = set(record.get('_oai', {}).get('sets', []))
    for spec in _build_cache():
        if spec in record_sets:
            yield spec

    # get list of sets that match using percolator
    index, doc_type = RecordIndexer().record_to_index(record)
    body = {"doc": record.dumps()}

    if ES_VERSION[0] > 2:
        current_search_client.indices.put_mapping(
            index=index, doc_type=PERCOLATOR_DOC_TYPE,
            body=PERCOLATOR_MAPPING, ignore=[400, 404])
    results = current_search_client.percolate(
        index=index, doc_type=doc_type, allow_no_indices=True,
        ignore_unavailable=True, body=body
    )
    prefix = 'oaiset-'
    prefix_len = len(prefix)
    for match in results['matches']:
        set_name = match['_id']
        if set_name.startswith(prefix):
            name = set_name[prefix_len:]
            yield name

    raise StopIteration
