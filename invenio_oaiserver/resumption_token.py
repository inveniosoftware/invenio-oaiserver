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

import random

from flask import current_app
from itsdangerous import URLSafeTimedSerializer
from marshmallow import Schema, fields


def serialize(pagination, **kwargs):
    """Return resumtion token serializer."""
    from .verbs import Verbs

    if not pagination.has_next:
        return

    token_builder = URLSafeTimedSerializer(
        current_app.config['SECRET_KEY'],
        salt=kwargs['verb'],
    )
    schema = getattr(Verbs, kwargs['verb'])(partial=False)
    data = dict(seed=random.random(), page=pagination.next_num,
                kwargs=schema.dumps(kwargs))
    scroll_id = getattr(pagination, '_scroll_id', None)
    if scroll_id:
        data['scroll_id'] = scroll_id

    return token_builder.dumps(data)


class ResumptionToken(fields.Field):
    """Resumption token validator."""

    def _deserialize(self, value, attr, data):
        """Serialize resumption token."""
        token_builder = URLSafeTimedSerializer(
            current_app.config['SECRET_KEY'],
            salt=data['verb'],
        )
        data = token_builder.loads(value, max_age=current_app.config[
            'OAISERVER_RESUMPTION_TOKEN_EXPIRE_TIME'])
        data['token'] = value
        data['kwargs'] = self.root.load(data['kwargs'], partial=True).data
        return data


class ResumptionTokenSchema(Schema):
    """Schema with resumption token."""

    resumptionToken = ResumptionToken(required=True, load_only=True)

    def load(self, data, many=None, partial=None):
        """Deserialize a data structure to an object."""
        result = super(ResumptionTokenSchema, self).load(
            data, many=many, partial=partial
        )
        result.data.update(
            result.data.get('resumptionToken', {}).get('kwargs', {})
        )
        return result
