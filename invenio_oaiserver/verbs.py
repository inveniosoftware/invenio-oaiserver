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

"""OAI-PMH verbs."""

from __future__ import absolute_import

from flask import current_app
from marshmallow import Schema, ValidationError, fields, validates_schema

from .resumption_token import ResumptionTokenSchema


def validate_metadata_prefix(value):
    """Check metadataPrefix."""
    metadataFormats = current_app.config['OAISERVER_METADATA_FORMATS']
    if value not in metadataFormats:
        raise ValidationError('metadataPrefix does not exist',
                              field_names=['metadataPrefix'])


class OAISchema(Schema):
    """Base OAI argument schema."""

    verb = fields.Str(required=True, load_only=True)

    class Meta:
        """Schema configuration."""

        strict = True

    @validates_schema
    def validate(self, data):
        """Check range between dates under keys ``from_`` and ``until``."""
        if 'verb' in data and data['verb'] != self.__class__.__name__:
            raise ValidationError(
                # FIXME encode data
                'This is not a valid OAI-PMH verb:{0}'.format(data['verb']),
                field_names=['verb'],
            )

        if 'from_' in data and 'until' in data and \
                data['from_'] > data['until']:
            raise ValidationError('Date from_ must be before until.')

        extra = set(data.keys()) - set(self.fields.keys())
        if extra:
            raise ValidationError('You have passed too many arguments.')


class Verbs(object):
    """List valid verbs and its arguments."""

    class GetRecord(OAISchema):
        """Arguments for GetRecord verb."""

        identifier = fields.Str(required=True)
        metadataPrefix = fields.Str(required=True,
                                    validate=validate_metadata_prefix)

    class GetMetadata(OAISchema):
        """Arguments for GetMetadata verb."""

        identifier = fields.Str(required=True)
        metadataPrefix = fields.Str(required=True,
                                    validate=validate_metadata_prefix)

    class Identify(OAISchema):
        """Arguments for Identify verb."""

    class ListIdentifiers(OAISchema):
        """Arguments for ListIdentifiers verb."""

        from_ = fields.DateTime(load_from='from', dumpt_to='from')
        until = fields.DateTime()
        set = fields.Str()
        metadataPrefix = fields.Str(required=True,
                                    validate=validate_metadata_prefix)

    class ListMetadataFormats(OAISchema):
        """Arguments for ListMetadataFormats verb."""

        identifier = fields.Str()

    class ListRecords(OAISchema):
        """Arguments for ListRecords verb."""

        from_ = fields.DateTime(load_from='from', dump_to='from')
        until = fields.DateTime()
        set = fields.Str()
        metadataPrefix = fields.Str(required=True,
                                    validate=validate_metadata_prefix)

    class ListSets(OAISchema):
        """Arguments for ListSets verb."""


class ResumptionVerbs(Verbs):
    """List valid verbs when resumtion token is defined."""

    class ListIdentifiers(OAISchema, ResumptionTokenSchema):
        """Arguments for ListIdentifiers verb."""

    class ListRecords(OAISchema, ResumptionTokenSchema):
        """Arguments for ListRecords verb."""

    class ListSets(OAISchema, ResumptionTokenSchema):
        """Arguments for ListSets verb."""


def make_request_validator(request):
    """Validate arguments in incomming request."""
    verb = request.values.get('verb', '', type=str)
    resumption_token = request.values.get('resumptionToken', None)

    schema = Verbs if resumption_token is None else ResumptionVerbs
    validator = getattr(schema, verb, OAISchema)(partial=False)
    # Force schema validation.
    validator.validate(request.args)
    return validator
