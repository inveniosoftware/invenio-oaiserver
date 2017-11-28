# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Percolator."""

from __future__ import absolute_import, print_function

from invenio_indexer.api import RecordIndexer
from invenio_search import current_search, current_search_client

from .models import OAISet
from .proxies import current_oaiserver
from .query import query_string_parser


def _new_percolator(spec, search_pattern):
    """Create new percolator associated with the new set."""
    if spec and search_pattern:
        query = query_string_parser(search_pattern=search_pattern).to_dict()
        for name in current_search.mappings.keys():
            current_search.client.index(
                index=name, doc_type='.percolator',
                id='oaiset-{}'.format(spec),
                body={'query': query}
            )


def _delete_percolator(spec, search_pattern):
    """Delete percolator associated with the new oaiset.

    :param target: Collection where the percolator was attached.
    """
    if spec:
        for name in current_search.mappings.keys():
            current_search.client.delete(
                index=name, doc_type='.percolator',
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
