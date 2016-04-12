# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
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

"""Utilities."""

from __future__ import absolute_import, print_function

from functools import partial

import six
from flask import current_app
from werkzeug.utils import import_string

try:
    from functools import lru_cache
except ImportError:  # pragma: no cover
    from functools32 import lru_cache


def parser():
    """Return search query parser."""
    query_parser = current_app.config['OAISERVER_QUERY_PARSER']
    if isinstance(query_parser, six.string_types):
        query_parser = import_string(query_parser)
        return query_parser


def query_walkers():
    """Return query walker instances."""
    return [
        import_string(walker)() if isinstance(walker, six.string_types)
        else walker() for walker in current_app.config[
            'OAISERVER_QUERY_WALKERS']
    ]


@lru_cache(maxsize=100)
def serializer(metadata_prefix):
    """Return etree_dumper instances."""
    metadataFormats = current_app.config['OAISERVER_METADATA_FORMATS']
    serializer_ = metadataFormats[metadata_prefix]['serializer']
    if isinstance(serializer_, tuple):
        return partial(import_string(serializer_[0]), **serializer_[1])
    return import_string(serializer_)


def dumps_etree(pid, record, **kwargs):
    """Dump MARC21 compatible record."""
    from dojson.contrib.to_marc21 import to_marc21
    from dojson.contrib.to_marc21.utils import dumps_etree

    return dumps_etree(to_marc21.do(record['_source']), **kwargs)


def datetime_to_datestamp(dt, day_granularity=False):
    """Transform datetime to datestamp."""
    # assert dt.tzinfo is None  # only accept timezone naive datetimes
    # ignore microseconds
    dt = dt.replace(microsecond=0)
    result = dt.isoformat() + 'Z'
    if day_granularity:
        result = result[:-10]
    return result
