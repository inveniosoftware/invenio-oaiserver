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

OAISERVER_GRANULARITY = 'YYYY-MM-DDThh:mm:ssZ'
"""The finest harvesting granularity supported by the repository.

The legitimate values are ``YYYY-MM-DD`` and ``YYYY-MM-DDThh:mm:ssZ``
with meanings as defined in ISO8601.
"""

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
            'invenio_oaiserver.utils:dumps_etree', {
                'xslt_filename': pkg_resources.resource_filename(
                    'invenio_oaiserver', 'static/xsl/MARC21slim2OAIDC.xsl'
                ),
            }
        ),
        'schema': 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
        'namespace': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
    },
    'marc21': {
        'serializer': (
            'invenio_oaiserver.utils:dumps_etree', {
                'prefix': 'marc',
            }
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

.. note::

    If you are migrating an instance running older versions of Invenio<=2.1,
    you might want to copy settings from ``'marc21'`` key to ``'marcxml'``
    in order to ensure compatibility for all your OAI-PMH clients.

"""

OAISERVER_REGISTER_RECORD_SIGNALS = True
"""Catch record/set insert/update/delete signals and update the `_oai`
field."""

OAISERVER_REGISTER_SET_SIGNALS = True
"""Catch set insert/update/delete signals and update the `_oai` record
field."""

OAISERVER_QUERY_PARSER = 'invenio_query_parser.parser:Main'
"""Define query parser for OIASet definition."""

OAISERVER_QUERY_WALKERS = [
    'invenio_query_parser.walkers.pypeg_to_ast:PypegConverter',
]
"""List of query AST walkers."""

OAISERVER_CACHE_KEY = 'DynamicOAISets::'
"""Key prefix added before all keys in cache server."""

OAISERVER_CELERY_TASK_CHUNK_SIZE = 100
"""Specify the maximum number of records each task will update."""
