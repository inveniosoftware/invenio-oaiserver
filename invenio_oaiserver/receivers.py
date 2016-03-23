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

"""Record field function."""

from __future__ import absolute_import, print_function

from datetime import datetime

from flask import current_app
from six import iteritems

from .models import OAISet
from .proxies import current_oaiserver
from .query import Query
from .response import datetime_to_datestamp
from .tasks import update_affected_records

try:
    from functools import lru_cache
except ImportError:  # pragma: no cover
    from functools32 import lru_cache


@lru_cache(maxsize=1000)
def _build_query(search_pattern):
    """Build ``Query`` object for given set query."""
    return Query(search_pattern)


def _build_cache():
    """Preprocess set queries."""
    for _set in OAISet.query.all():
        yield _set.spec, dict(
            query=_set.search_pattern,
        )
    raise StopIteration


def _find_matching_sets_internally(sets, record):
    """Find matching sets with internal engine.

    :param sets: set of sets where search
    :param record: record to match
    """
    record_sets = set(record.get('_oai', {}).get('sets', []))

    for spec, data in iteritems(sets):
        if data['query'] is None:
            is_correct = spec in record_sets
        else:
            is_correct = _build_query(data['query']).match(record)

        if is_correct:
            yield set((spec, ))
    raise StopIteration


def get_record_sets(record, matcher):
    """Return list of sets to which record belongs to.

    :param record: Record instance
    :return: list of set names
    """
    sets = current_oaiserver.sets
    if sets is None:
        # build sets cache
        sets = current_oaiserver.sets = dict(_build_cache())

    output = set()

    for sets in matcher(sets, record):
        output |= sets

    return list(output)


class OAIServerUpdater(object):
    """Return the right update oaisets function."""

    def __init__(self, app=None):
        """Init."""
        self.matcher = _find_matching_sets_internally

    def __call__(self, record, **kwargs):
        """Update sets list."""
        record.setdefault('_oai', {})
        record['_oai'].update({
            'sets': get_record_sets(record=record, matcher=self.matcher),
            'updated': datetime_to_datestamp(datetime.utcnow()),
        })


def after_insert_oai_set(mapper, connection, target):
    """Update records on OAISet insertion."""
    update_affected_records.delay(
        search_pattern=target.search_pattern
    )


def after_update_oai_set(mapper, connection, target):
    """Update records on OAISet update."""
    update_affected_records.delay(
        spec=target.spec, search_pattern=target.search_pattern
    )


def after_delete_oai_set(mapper, connection, target):
    """Update records on OAISet deletion."""
    update_affected_records.delay(
        spec=target.spec
    )
