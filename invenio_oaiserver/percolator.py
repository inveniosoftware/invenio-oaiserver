# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Percolator."""

from __future__ import absolute_import, print_function

import json

from elasticsearch import VERSION as ES_VERSION
from elasticsearch.helpers.actions import scan
from flask import current_app
from invenio_indexer.api import RecordIndexer
from invenio_indexer.utils import schema_to_index
from invenio_search import current_search, current_search_client
from invenio_search.utils import build_index_name

from invenio_oaiserver.query import query_string_parser

from .models import OAISet
from .proxies import current_oaiserver


def _build_percolator_index_name(index):
    """Build percolator index name."""
    suffix = "-percolators"
    if ES_VERSION[0] < 7:
        suffix = ""
    return build_index_name(index, suffix=suffix, app=current_app)


def _create_percolator_mapping(index, doc_type, mapping_path=None):
    """Update mappings with the percolator field.

    .. note::

        This is only needed from ElasticSearch v5 onwards, because percolators
        are now just a special type of field inside mappings.
    """
    percolator_index = _build_percolator_index_name(index)
    if ES_VERSION[0] in (5, 6):
        current_search_client.indices.put_mapping(
            index=index, doc_type=doc_type, body=PERCOLATOR_MAPPING
        )
    elif ES_VERSION[0] == 7:
        if not mapping_path:
            mapping_path = current_search.mappings[index]
        if not current_search_client.indices.exists(percolator_index):
            with open(mapping_path, 'r') as body:
                mapping = json.load(body)
                mapping["mappings"]["properties"].update(
                    PERCOLATOR_MAPPING["properties"]
                )
                current_search_client.indices.create(
                    index=percolator_index, body=mapping
                )


def _percolate_query(index, doc_type, percolator_doc_type, document):
    """Get results for a percolate query."""
    index = _build_percolator_index_name(index)
    if ES_VERSION[0] in (2, 5):
        results = current_search_client.percolate(
            index=index,
            doc_type=doc_type,
            allow_no_indices=True,
            ignore_unavailable=True,
            body={'doc': document},
        )
        return results['matches']
    elif ES_VERSION[0] in (6, 7):
        es_client_params = dict(
            index=index,
            doc_type=percolator_doc_type,
            allow_no_indices=True,
            ignore_unavailable=True,
            body={
                'query': {
                    'percolate': {
                        'field': 'query',
                        'document_type': percolator_doc_type,
                        'document': document,
                    }
                }
            },
        )
        if ES_VERSION[0] == 7:
            es_client_params.pop('doc_type')
        results = current_search_client.search(**es_client_params)
        return results['hits']['hits']


def _get_percolator_doc_type(index):
    es_ver = ES_VERSION[0]
    if es_ver == 2:
        return '.percolator'
    elif es_ver == 5:
        return 'percolators'
    elif es_ver in (6, 7):
        mapping_path = current_search.mappings[index]
        _, doc_type = schema_to_index(mapping_path)
        return doc_type


PERCOLATOR_MAPPING = {'properties': {'query': {'type': 'percolator'}}}


def _new_percolator(spec, search_pattern):
    """Create new percolator associated with the new set."""
    if spec and search_pattern:
        query = query_string_parser(search_pattern=search_pattern).to_dict()
        for index, mapping_path in current_search.mappings.items():
            # Create the percolator doc_type in the existing index for >= ES5
            # TODO: Consider doing this only once in app initialization
            try:
                percolator_doc_type = _get_percolator_doc_type(index)
                _create_percolator_mapping(
                    index, percolator_doc_type, mapping_path)
                current_search_client.index(
                    index=_build_percolator_index_name(index),
                    doc_type=percolator_doc_type,
                    id='oaiset-{}'.format(spec),
                    body={'query': query}
                )
            except:
                # caught on schemas, which do not contain the query field
                pass


def _delete_percolator(spec, search_pattern):
    """Delete percolator associated with the removed/updated oaiset."""
    # Create the percolator doc_type in the existing index for >= ES5
    for index, mapping_path in current_search.mappings.items():
        percolator_doc_type = _get_percolator_doc_type(index)
        _create_percolator_mapping(index, percolator_doc_type)
        current_search_client.delete(
            index=_build_percolator_index_name(index),
            doc_type=percolator_doc_type,
            id='oaiset-{}'.format(spec),
            ignore=[404],
        )


def create_percolate_query(
    percolator_ids=None, documents=None, document_es_ids=None, document_es_indices=None
):
    """Create percolate query for provided arguments."""
    queries = []
    # documents or (document_es_ids and document_es_indices) has to be set
    if documents is not None:
        queries.append(
            {
                "percolate": {
                    "field": "query",
                    "documents": documents,
                }
            }
        )
    elif (
        document_es_ids is not None and document_es_indices
        is not None and len(document_es_ids) == len(document_es_indices)
    ):
        queries.extend(
            [
                {
                    "percolate": {
                        "field": "query",
                        "index": es_index,
                        "id": es_id,
                        "name": f"{es_index}:{es_id}",
                    }
                }
                for (es_id, es_index) in zip(document_es_ids, document_es_indices)
            ]
        )
    else:
        raise Exception(
            "Either documents or (document_es_ids and document_es_indices) must be specified."
        )

    if percolator_ids:
        queries.append({"ids": {"values": percolator_ids}})

    query = {"query": {"bool": {"must": queries}}}

    return query


def percolate_query(
    percolator_index,
    percolator_ids=None,
    documents=None,
    document_es_ids=None,
    document_es_indices=None,
):
    """Get results for a percolate query."""
    query = create_percolate_query(
        percolator_ids=percolator_ids,
        documents=documents,
        document_es_ids=document_es_ids,
        document_es_indices=document_es_indices,
    )
    result = scan(
        current_search_client,
        index=percolator_index,
        query=query,
        scroll="1m",
    )
    return result


def sets_search_all(records):
    """Retrieve sets for provided records."""
    if not records:
        return []

    # records should all have the same index. maybe add index as parameter?
    record_index, doc_type = RecordIndexer()._record_to_index(records[0])
    _create_percolator_mapping(record_index, doc_type)
    percolator_index = _build_percolator_index_name(record_index)
    record_sets = [[] for _ in range(len(records))]

    result = percolate_query(percolator_index, documents=records)

    prefix = 'oaiset-'
    prefix_len = len(prefix)

    for s in result:
        set_index_id = s["_id"]
        if set_index_id.startswith(prefix):
            set_spec = set_index_id[prefix_len:]
            for record_index in s.get("fields", {}).get(
                "_percolator_document_slot", []
            ):
                record_sets[record_index].append(set_spec)
    return record_sets


def find_sets_for_record(record):
    """Fetch a record's sets."""
    return sets_search_all([record])[0]


# TODO: Remove everything below before merging
def remove_sets():
    """Remove specified sets."""
    from invenio_db import db

    specs = []
    index = current_app.config.get('OAISERVER_RECORD_INDEX')

    for spec in specs:
        try:
            db_set = OAISet.query.filter_by(spec=spec).one()
            print(db_set)
            db.session.delete(db_set)
            db.session.commit()
        except Exception as e:
            print(f"Exception during set removal ({spec}):", e)

        _delete_percolator(spec, "***")
        current_search_client.delete(
            index=_build_percolator_index_name(index), id=spec, ignore=[404]
        )


def create_new_set():
    """Create a new set."""
    from datetime import datetime

    from invenio_db import db

    name = f"published-{datetime.now()}"
    s = OAISet(
        spec=name,
        name=name,
        description="created via python orm",
        search_pattern="is_published:true",
    )
    db.session.add(s)
    db.session.commit()


import time


def index_sets():
    """Index all sets."""
    sets = OAISet.query.all()
    if not sets:
        return []

    x0 = time.time()
    num_total = len(sets)
    for index, set in enumerate(sets):
        _new_percolator(set.spec, set.search_pattern)
        print_estimated_time(x0, num_total, index)


def print_estimated_time(start_time, num_total_elements, num_current_element):
    """Calculate and print estimated remaining time."""
    current_time = time.time()
    total_time_so_far = current_time - start_time
    average_time = total_time_so_far / (num_current_element + 1)
    estimated_time = (num_total_elements - num_current_element) * average_time
    print(
        f"{num_current_element}/{num_total_elements} took {total_time_so_far:.2f}. Estimate: {estimated_time:.2f}"
    )
