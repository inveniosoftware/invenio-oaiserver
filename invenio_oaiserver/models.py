# SPDX-FileCopyrightText: 2015-2025 CERN.
# SPDX-FileCopyrightText: 2022-2026 Graz University of Technology.
# SPDX-FileCopyrightText: 2024 KTH Royal Institute of Technology.
# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Models for storing information about OAIServer state."""

import sqlalchemy as sa
from invenio_db import db
from invenio_i18n import lazy_gettext as _
from sqlalchemy.orm import validates

from .errors import OAISetSpecUpdateError


class OAISet(db.Model, db.Timestamp):
    """Information about OAI set."""

    __tablename__ = "oaiserver_set"

    id = db.Column(db.Integer, primary_key=True)

    spec = db.Column(
        db.String(255),
        nullable=False,
        unique=True,
        info=dict(
            label=_("Identifier"),
            description=_("Identifier of the set."),
        ),
    )
    """Set identifier."""

    name = db.Column(
        db.String(255),
        info=dict(
            label=_("Long name"),
            description=_("Long name of the set."),
        ),
        index=True,
    )
    """Human readable name of the set."""

    description = db.Column(
        db.Text,
        nullable=True,
        info=dict(
            label=_("Description"),
            description=_("Description of the set."),
        ),
    )
    """Human readable description."""

    search_pattern = db.Column(
        db.Text,
        nullable=True,
        info=dict(
            label=_("Search pattern"),
            description=_("Search pattern to select records"),
        ),
    )
    """Search pattern to get records."""

    system_created = db.Column(
        db.Boolean,
        nullable=False,
        server_default=sa.sql.expression.literal(False),
        info=dict(
            label=_("System created"),
            description=_("System created set"),
        ),
    )
    """System created field."""

    @validates("spec")
    def validate_spec(self, key, value):
        """Forbit updates of set identifier."""
        if self.spec and self.spec != value:
            raise OAISetSpecUpdateError(_("Updating spec is not allowed."))
        return value


__all__ = ("OAISet",)
