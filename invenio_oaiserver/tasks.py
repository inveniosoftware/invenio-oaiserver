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

"""Task for OAI."""

from celery import group, shared_task
from flask import current_app
from flask_celeryext import RequestContextTask
from invenio_db import db
from invenio_records.api import Record

from .query import get_affected_records

try:
    from itertools import zip_longest
except ImportError:  # pragma: no cover
    from itertools import izip_longest as zip_longest


@shared_task(base=RequestContextTask)
def update_records_sets(record_ids):
    """Update records sets."""
    for record_id in record_ids:
        record = Record.get_record(id=record_id)
        record.commit()
    db.session.commit()


@shared_task(base=RequestContextTask)
def update_affected_records(spec=None, search_pattern=None):
    """Update all affected records by OAISet change."""
    chunk_size = current_app.config['OAISERVER_CELERY_TASK_CHUNK_SIZE']
    record_ids = get_affected_records(spec=spec, search_pattern=search_pattern)

    group(
        update_records_sets.s(filter(None, chunk))
        for chunk in zip_longest(*[iter(record_ids)] * chunk_size)
    )()
