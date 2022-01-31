# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2022 CERN.
# Copyright (C) 2022 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Models for storing information about OAIServer state."""

from flask_babelex import lazy_gettext as _
from invenio_db import db
from sqlalchemy.orm import validates
from sqlalchemy_utils import Timestamp

from .errors import OAISetSpecUpdateError


class OAISet(db.Model, Timestamp):
    """Information about OAI set."""

    __tablename__ = 'oaiserver_set'

    id = db.Column(db.Integer, primary_key=True)

    spec = db.Column(
        db.String(255),
        nullable=False,
        unique=True,
        info=dict(
            label=_('Identifier'),
            description=_('Identifier of the set.'),
        ),
    )
    """Set identifier."""

    name = db.Column(
        db.String(255),
        info=dict(
            label=_('Long name'),
            description=_('Long name of the set.'),
        ),
        index=True,
    )
    """Human readable name of the set."""

    description = db.Column(
        db.Text,
        nullable=True,
        info=dict(
            label=_('Description'),
            description=_('Description of the set.'),
        ),
    )
    """Human readable description."""

    search_pattern = db.Column(
        db.Text,
        nullable=True,
        info=dict(
            label=_('Search pattern'),
            description=_('Search pattern to select records'),
        )
    )
    """Search pattern to get records."""

    @validates('spec')
    def validate_spec(self, key, value):
        """Forbit updates of set identifier."""
        if self.spec and self.spec != value:
            raise OAISetSpecUpdateError("Updating spec is not allowed.")
        return value

    # TODO: Add and remove can be implemented but it will require to
    # update the `search_pattern`

    # def add_record(self, record):
    #     """Add a record to the OAISet.

    #     :param record: Record to be added.
    #     :type record: `invenio_records.api.Record` or derivative.
    #     """
    #     record.setdefault('_oai', {}).setdefault('sets', [])

    #     assert not self.has_record(record)

    #     record['_oai']['sets'].append(self.spec)

    # def remove_record(self, record):
    #     """Remove a record from the OAISet.

    #     :param record: Record to be removed.
    #     :type record: `invenio_records.api.Record` or derivative.
    #     """
    #     assert self.has_record(record)

    #     record['_oai']['sets'] = [
    #         s for s in record['_oai']['sets'] if s != self.spec]

    # TODO: has_record can be implemented but it will require to
    # to do a full search.

    # def has_record(self, record):
    #     """Check if the record blongs to the OAISet.

    #     :param record: Record to be checked.
    #     :type record: `invenio_records.api.Record` or derivative.
    #     """
    #     return self.spec in record.get('_oai', {}).get('sets', [])


__all__ = ('OAISet', )
