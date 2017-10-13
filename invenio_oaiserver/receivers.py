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
from time import sleep

from .percolator import _delete_percolator, _new_percolator, get_record_sets
from .tasks import update_affected_records
from .utils import datetime_to_datestamp


class OAIServerUpdater(object):
    """Return the right update oaisets function."""

    def __call__(self, sender, record, **kwargs):
        """Update sets list.

        :param record: The record data.
        """
        if '_oai' in record and 'id' in record['_oai']:
            new_sets = set(get_record_sets(record=record))
            # Update only if old and new sets differ
            if set(record['_oai'].get('sets', [])) != new_sets:
                record['_oai'].update({
                    'sets': list(new_sets)
                })


def after_insert_oai_set(mapper, connection, target):
    """Update records on OAISet insertion."""
    _new_percolator(spec=target.spec, search_pattern=target.search_pattern)
    sleep(2)
    update_affected_records.delay(
        search_pattern=target.search_pattern
    )


def after_update_oai_set(mapper, connection, target):
    """Update records on OAISet update."""
    _delete_percolator(spec=target.spec, search_pattern=target.search_pattern)
    _new_percolator(spec=target.spec, search_pattern=target.search_pattern)
    sleep(2)
    update_affected_records.delay(
        spec=target.spec, search_pattern=target.search_pattern
    )


def after_delete_oai_set(mapper, connection, target):
    """Update records on OAISet deletion."""
    _delete_percolator(spec=target.spec, search_pattern=target.search_pattern)
    sleep(2)
    update_affected_records.delay(
        spec=target.spec
    )
