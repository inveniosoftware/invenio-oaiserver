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

"""The details of the configuration options for OAI-PMH server."""

import pkg_resources

OAISERVER_PAGE_SIZE = 10
"""Define maximum length of list responses.

Request with verbs ``ListRecords``, ``ListIdentifiers``, and ``ListSets``
are affected by this option.
"""

OAISERVER_RECORD_INDEX = 'records'
"""Specify an Elastic index with records that should be exposed via OAI-PMH."""

# The version of the OAI-PMH supported by the repository.
OAISERVER_PROTOCOL_VERSION = '2.0'

OAISERVER_ADMIN_EMAILS = [
    'info@invenio-software.org',
]
"""The e-mail addresses of administrators of the repository.

It **must** include one or more instances.
"""

# TODO Add support for compressions.
OAISERVER_COMPRESSIONS = [
    'identity',
]

OAISERVER_RESUMPTION_TOKEN_EXPIRE_TIME = 1 * 60
"""The expiration time of a resuption token in seconds.

**Default: 60 seconds = 1 minute**.

.. note::

    Setting longer expiration time may have a negative impact on your
    Elastic search cluster as it might need to keep open cursors.

    https://www.elastic.co/guide/en/elasticsearch/reference/current/search-request-scroll.html
"""

OAISERVER_METADATA_FORMATS = {
    'oai_dc': {
        'serializer': (
            'dojson.contrib.to_marc21.utils:dumps_etree',
            {
                'xslt_filename': pkg_resources.resource_filename(
                    'invenio_oaiserver', 'static/xsl/oai2.v1.0.xsl')
            }
        ),
        'schema': 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
        'namespace': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
    },
    'marcxml': {
        'serializer': (
            'dojson.contrib.to_marc21.utils:dumps_etree',
        ),
        'schema': 'http://www.loc.gov/standards/marcxml/schema/MARC21slim.xsd',
        'namespace': 'http://www.loc.gov/MARC21/slim',
    }
}
"""Define the metadata formats available from a repository.

Every key represents a ``metadataPrefix`` and its value has a following
structure.

* ``schema`` - the location of an XML Schema describing the format;
* ``namespace`` - the namespace of serialized document;
* ``serializer`` - the importable string or tuple with the importable string
  and keyword arguments.
"""

OAISERVER_REGISTER_RECORD_SIGNALS = True
"""Catch record insert/update signals and update the `_oai` field."""

OAISERVER_QUERY_PARSER = 'invenio_query_parser.parser:Main'
"""Define query parser for OIASet definition."""

OAISERVER_QUERY_WALKERS = [
    'invenio_query_parser.walkers.pypeg_to_ast:PypegConverter',
]
"""List of query AST walkers."""

try:
    pkg_resources.get_distribution('invenio_search')

    from invenio_search.config import \
        SEARCH_QUERY_PARSER as OAISERVER_QUERY_PARSER, \
        SEARCH_QUERY_WALKERS as OAISERVER_QUERY_WALKERS
except pkg_resources.DistributionNotFound:  # pragma: no cover
    pass

OAISERVER_CACHE_KEY = 'DynamicOAISets::'
"""Key prefix added before all keys in cache server."""
