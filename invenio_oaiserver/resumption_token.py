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

"""Implement funtions for managing OAI-PMH resumption token."""

from flask import current_app, request
from itsdangerous import URLSafeTimedSerializer
from marshmallow import fields


def serialize(has_next=True, **kwargs):
    """Return resumtion token serializer."""
    if not has_next:
        return

    # TODO completeListSize and cursor
    page = 2  # first build token for next page

    if 'resumptionToken' in kwargs:
        page = kwargs['resumptionToken']['page'] + 1
        del kwargs['resumptionToken']

    for key in ('from_', 'until'):
        if key in kwargs:
            kwargs[key] = request.args.get(key)

    token_builder = URLSafeTimedSerializer(
        current_app.config['SECRET_KEY'],
        salt=kwargs['verb'],
    )
    return token_builder.dumps(dict(kwargs=kwargs, page=page))


class ResumptionToken(fields.Field):
    """Resumption token validator."""

    def _deserialize(self, value, attr, data):
        """Serialize resumption token."""
        token_builder = URLSafeTimedSerializer(
            current_app.config['SECRET_KEY'],
            salt=data['verb'],
        )
        data = token_builder.loads(value)
        data['token'] = value
        return data
