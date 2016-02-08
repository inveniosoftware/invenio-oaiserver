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
from invenio_records.models import RecordMetadata
from invenio_search import Query as SearchQuery
from invenio_search import current_search_client
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.utils import cached_property

from .utils import parser, query_walkers


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
            # FIXME retrieve from elastic search
            "updated": RecordMetadata.query.filter_by(
                id=result['_id']).one().updated
        }


def get_record(recid):
    """Get a record."""
    response = current_search_client.get(
        index=current_app.config['OAISERVER_RECORD_INDEX'],
        id=recid
        # version=True,
    )
    try:
        result = response['hits']['hits'][0]
    except TypeError:
        raise NoResultFound()

    return {
        "id": result['_id'],
        "json": result['_source'],
        # FIXME retrieve from elastic search
        "updated": RecordMetadata.query.filter_by(
            id=result['_id']).one().updated
    }
