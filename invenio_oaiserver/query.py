# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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
# 59 Temple Place, Suite 330, Boston, MA 02D111-1307, USA.

"""Query parser."""

import pypeg2
from flask import current_app
from invenio_query_parser.walkers.match_unit import MatchUnit
from invenio_search import Query as SearchQuery
from invenio_search import current_search_client
from werkzeug.utils import cached_property

from .utils import datestamp_to_datetime, parser, query_walkers


class Query(SearchQuery):
    """Query object."""

    @cached_property
    def query(self):
        """Parse query string using given grammar."""
        tree = pypeg2.parse(self._query, parser(), whitespace="")
        for walker in query_walkers():
            tree = tree.accept(walker)
        return tree

    def match(self, record):
        """Return True if record match the query."""
        return self.query.accept(MatchUnit(record))


def get_records(page=1):
    """Get records."""
    size = current_app.config['OAISERVER_PAGE_SIZE']
    query = Query()[(page-1)*size:page*size]

    response = current_search_client.search(
        index=current_app.config['OAISERVER_RECORD_INDEX'],
        body=query.body,
        # version=True,
    )

    for result in response['hits']['hits']:
        yield {
            "id": result['_id'],
            "json": result['_source'],
            "updated": datestamp_to_datetime(result['_source']['_updated'])
        }


def get_record_by_oaiid(oaiid):
    """Get record by oaiid."""
    query = {'match_all': {"_oaiid": oaiid}}
    response = current_search_client.search(
        index=current_app.config['OAISERVER_RECORD_INDEX'],
        body={'query': query}
        # version=True,
    )
    result = response['hits']['hits'][0]
    return {
        "id": result['_id'],
        "json": result['_source'],
        "updated": datestamp_to_datetime(result['_source']['_updated'])
    }


def get_record(recid):
    """Get a record."""
    if recid:
        response = current_search_client.get(
            index=current_app.config['OAISERVER_RECORD_INDEX'],
            id=str(recid)
            # version=True,
        )
    return {
        "id": response['_id'],
        "json": response['_source'],
        "updated": datestamp_to_datetime(response['_source']['_updated'])
    }
