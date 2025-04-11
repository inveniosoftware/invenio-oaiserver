# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2025 CERN.
# Copyright (C) 2022 Graz University of Technology.
# Copyright (C) 2024 KTH Royal Institute of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Percolator."""

import json

from flask import current_app
from invenio_i18n import lazy_gettext as _
from invenio_search import current_search, current_search_client
from invenio_search.engine import search
from invenio_search.utils import build_index_name

from invenio_oaiserver.query import query_string_parser


def _build_percolator_index_name(index):
    """Build percolator index name."""
    # For backward compatibility only: percolators used to be written into a different index, with the suffix
    # `-percolators`. In recent versions, the percolators can coexist in the same indices as the records

    percolator_index = build_index_name(index, suffix="", app=current_app)
    if current_search_client.indices.exists(f"{percolator_index}-percolators"):
        percolator_index = f"{percolator_index}-percolators"
    # If it does not exist, but we want it, we create it
    elif current_app.config["OAISERVER_PERCOLATOR_DEDICATED_INDEX"]:
        percolator_index = f"{percolator_index}-percolators"
        mapping_path = current_search.mappings[index]
        with open(mapping_path, "r") as body:
            mapping = json.load(body)
            current_search_client.indices.create(index=percolator_index, body=mapping)

    # Let's check as well that the mapping for `query` exists. It would be better if this was done only once
    # The main issue is that the first time could be either creating a set, or querying if a record is in any set
    mapping = current_search_client.indices.get_field_mapping(
        index=percolator_index, fields="query"
    )
    if (
        not percolator_index in mapping
        or "query" not in mapping[percolator_index]["mappings"]
    ):
        # The field is not there. Adding the mapping
        current_search_client.indices.put_mapping(
            index=percolator_index,
            body={"properties": {"query": {"type": "percolator"}}},
        )
    return percolator_index


def _new_percolator(spec, search_pattern):
    """Create new percolator associated with the new set."""
    if spec and search_pattern:
        query = query_string_parser(search_pattern=search_pattern).to_dict()

        # NOTE: We call `str` so that we can also handle lazy values (e.g. a LocalProxy)
        oai_records_index = str(current_app.config["OAISERVER_RECORD_INDEX"])
        for index, _ in (
            current_search.mappings.items() | current_search.index_templates.items()
        ):
            # Skip indices/mappings not used by OAI-PMH
            if not index.startswith(oai_records_index):
                continue
            try:
                percolator_index = _build_percolator_index_name(index)
                current_search_client.index(
                    index=percolator_index,
                    id="oaiset-{}".format(spec),
                    body={"query": query},
                )
            except Exception as e:
                current_app.logger.warning(e)


def _delete_percolator(spec, search_pattern):
    """Delete percolator associated with the removed/updated oaiset."""
    # NOTE: We call `str` so that we can also handle lazy values (e.g. a LocalProxy)
    oai_records_index = str(current_app.config["OAISERVER_RECORD_INDEX"])
    # Create the percolator doc_type in the existing index for >= ES5
    for index, _ in (
        current_search.mappings.items() | current_search.index_templates.items()
    ):
        # Skip indices/mappings not used by OAI-PMH
        if not index.startswith(oai_records_index):
            continue
        current_search_client.delete(
            index=_build_percolator_index_name(index),
            id="oaiset-{}".format(spec),
            ignore=[404],
        )


def create_percolate_query(
    percolator_ids=None,
    documents=None,
    document_search_ids=None,
    document_search_indices=None,
):
    """Create percolate query for provided arguments."""
    queries = []
    # documents or (document_search_ids and document_search_indices) has to be set
    # TODO: discuss if this is needed or documents alone is enough.
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
        document_search_ids is not None
        and document_search_indices is not None
        and len(document_search_ids) == len(document_search_indices)
    ):
        queries.extend(
            [
                {
                    "percolate": {
                        "field": "query",
                        "index": search_index,
                        "id": search_id,
                        "name": f"{search_index}:{search_id}",
                    }
                }
                for (search_id, search_index) in zip(
                    document_search_ids, document_search_indices
                )
            ]
        )
    else:
        raise Exception(
            _(
                "Either documents or (document_search_ids and document_search_indices) must be specified."
            )
        )

    if percolator_ids:
        queries.append({"ids": {"values": percolator_ids}})

    query = {"query": {"bool": {"must": queries}}}
    return query


def percolate_query(
    percolator_index,
    percolator_ids=None,
    documents=None,
    document_search_ids=None,
    document_search_indices=None,
):
    """Get results for a percolate query."""
    query = create_percolate_query(
        percolator_ids=percolator_ids,
        documents=documents,
        document_search_ids=document_search_ids,
        document_search_indices=document_search_indices,
    )
    result = search.helpers.scan(
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

    record_index = str(current_app.config["OAISERVER_RECORD_INDEX"])
    percolator_index = _build_percolator_index_name(record_index)
    record_sets = [[] for _ in range(len(records))]
    result = percolate_query(percolator_index, documents=records)
    prefix = "oaiset-"
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
