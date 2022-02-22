# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2022 CERN.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Percolator."""

import json

from elasticsearch import VERSION as ES_VERSION
from elasticsearch.helpers.actions import scan
from flask import current_app
from invenio_indexer.api import RecordIndexer
from invenio_indexer.utils import schema_to_index
from invenio_search import current_search, current_search_client
from invenio_search.utils import build_index_name

from invenio_oaiserver.query import query_string_parser


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
        oai_records_index = current_app.config["OAISERVER_RECORD_INDEX"]
        for index, mapping_path in current_search.mappings.items():
            # Skip indices/mappings not used by OAI-PMH
            if not index.startswith(oai_records_index):
                continue
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
            except Exception as e:
                current_app.logger.warning(e)


def _delete_percolator(spec, search_pattern):
    """Delete percolator associated with the removed/updated oaiset."""
    oai_records_index = current_app.config["OAISERVER_RECORD_INDEX"]
    # Create the percolator doc_type in the existing index for >= ES5
    for index, mapping_path in current_search.mappings.items():
        # Skip indices/mappings not used by OAI-PMH
        if not index.startswith(oai_records_index):
            continue
        percolator_doc_type = _get_percolator_doc_type(index)
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
    # TODO: discuss if this is needed or documents alone is enough.
    if documents is not None:
        queries.append({
            "percolate": {
                "field": "query",
                "documents": documents,
            }
        })
    elif (
        document_es_ids is not None and document_es_indices
        is not None and len(document_es_ids) == len(document_es_indices)
    ):
        queries.extend([{
            "percolate": {
                "field": "query",
                "index": es_index,
                "id": es_id,
                "name": f"{es_index}:{es_id}",
            }
        } for (es_id, es_index) in zip(document_es_ids, document_es_indices)])
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

    # TODO: records should all have the same index. maybe add index as parameter?
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
