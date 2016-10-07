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

"""Persistent identifier minters."""

from __future__ import absolute_import, print_function

from datetime import datetime

from flask import current_app
from invenio_pidstore import current_pidstore

from .provider import OAIIDProvider
from .utils import datetime_to_datestamp


def oaiid_minter(record_uuid, data):
    """Mint record identifiers.

    :param record_uuid: The record UUID.
    :param data: The record data.
    :returns: A :class:`invenio_pidstore.models.PersistentIdentifier` instance.
    """
    pid_value = data.get('_oai', {}).get('id')
    if pid_value is None:
        fetcher_name = \
            current_app.config.get('OAISERVER_CONTROL_NUMBER_FETCHER', 'recid')
        cn_pid = current_pidstore.fetchers[fetcher_name](record_uuid, data)
        pid_value = current_app.config.get('OAISERVER_ID_PREFIX', '') + str(
            cn_pid.pid_value
        )
    provider = OAIIDProvider.create(
        object_type='rec', object_uuid=record_uuid,
        pid_value=str(pid_value)
    )
    data.setdefault('_oai', {})
    data['_oai']['id'] = provider.pid.pid_value
    data['_oai']['updated'] = datetime_to_datestamp(datetime.utcnow())
    return provider.pid
