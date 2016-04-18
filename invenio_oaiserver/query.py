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
from elasticsearch.helpers import scan
from elasticsearch_dsl import Q
from flask import current_app
from invenio_query_parser.walkers.match_unit import MatchUnit
from invenio_search import RecordsSearch, current_search_client
from invenio_search.walkers.elasticsearch import ElasticSearchDSL
from werkzeug.utils import cached_property

from .utils import parser, query_walkers


class Query(object):
    """Query object."""

    def __init__(self, query=None):
        """Parse query string using given grammar."""
        tree = pypeg2.parse(query or '', parser(), whitespace='')
        for walker in query_walkers():
            tree = tree.accept(walker)
        self.query = tree

    def match(self, record):
        """Return True if record match the query."""
        return self.query.accept(MatchUnit(record))


class OAIServerSearch(RecordsSearch):
    """Define default filter for quering OAI server."""

    class Meta:
        """Configuration for OAI server search."""

        default_filter = Q('exists', field='_oai.id')


def get_affected_records(spec=None, search_pattern=None):
    """Get list of affected records."""
    # spec       pattern    query
    # ---------- ---------- -------
    # None       None       None
    # None       Y          Y
    # X          None       X
    # X          ''         X
    # X          Y          X OR Y

    if spec is None and search_pattern is None:
        raise StopIteration

    queries = []

    if spec is not None:
        queries.append(Q('match', **{'_oai.sets': spec}))

    if search_pattern:
        queries.append(Query(search_pattern).query.accept(ElasticSearchDSL()))

    search = OAIServerSearch(
        index=current_app.config['OAISERVER_RECORD_INDEX'],
    ).query(Q('bool', should=queries))

    for result in search.scan():
        yield result.meta.id


def get_records(**kwargs):
    """Get records."""
    page_ = kwargs.get('resumptionToken', {}).get('page', 1)
    size_ = current_app.config['OAISERVER_PAGE_SIZE']
    scroll = current_app.config['OAISERVER_RESUMPTION_TOKEN_EXPIRE_TIME']
    scroll_id = kwargs.get('resumptionToken', {}).get('scroll_id')

    if scroll_id is None:
        search = OAIServerSearch(
            index=current_app.config['OAISERVER_RECORD_INDEX'],
        ).params(
            scroll='{0}s'.format(scroll),
        ).extra(
            version=True,
        )[(page_-1)*size_:page_*size_]

        if 'set' in kwargs:
            search = search.query('match', **{'_oai.sets': kwargs['set']})

        time_range = {}
        if 'from_' in kwargs:
            time_range['gte'] = kwargs['from_']
        if 'until' in kwargs:
            time_range['lte'] = kwargs['until']
        if time_range:
            search = search.filter('range', **{'_oai.updated': time_range})

        response = search.execute().to_dict()
    else:
        response = current_search_client.scroll(
            scroll_id=scroll_id,
            scroll='{0}s'.format(scroll),
        )

    class Pagination(object):
        """Dummy pagination class."""

        page = page_
        per_page = size_

        def __init__(self, response):
            """Initilize pagination."""
            self.response = response
            self.total = response['hits']['total']
            self._scroll_id = response.get('_scroll_id')

            # clean descriptor on last page
            if not self.has_next:
                current_search_client.clear_scroll(
                    scroll_id=self._scroll_id
                )
                self._scroll_id = None

        @cached_property
        def has_next(self):
            """Return True if there is next page."""
            return self.page * self.per_page <= self.total

        @cached_property
        def next_num(self):
            """Return next page number."""
            return self.page + 1 if self.has_next else None

        @property
        def items(self):
            """Return iterator."""
            from datetime import datetime
            for result in self.response['hits']['hits']:
                if '_oai' in result['_source']:
                    yield {
                        'id': result['_id'],
                        'json': result,
                        'updated': datetime.strptime(
                            result['_source']['_oai']['updated'],
                            '%Y-%m-%dT%H:%M:%SZ'
                        ),
                    }

    return Pagination(response)
