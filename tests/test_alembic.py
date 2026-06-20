# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Test invenio-oaiserver alembic."""

import pytest
from invenio_db import db
from invenio_db.utils import alembic_test_context, drop_alembic_version_table


def test_alembic(app):
    """Test alembic recipes."""
    ext = app.extensions["invenio-db"]

    if db.engine.name == "sqlite":
        raise pytest.skip("Upgrades are not supported on SQLite.")

    app.config["ALEMBIC_CONTEXT"] = alembic_test_context()

    # Check that this package's SQLAlchemy models have been properly registered
    tables = [x for x in db.metadata.tables]
    assert "oaiserver_set" in tables

    # Check that Alembic agrees that there's no further tables to create.
    assert len(ext.alembic.compare_metadata()) == 0

    # Drop everything and recreate tables all with Alembic
    db.drop_all()
    drop_alembic_version_table()
    ext.alembic.upgrade()
    assert len(ext.alembic.compare_metadata()) == 0

    drop_alembic_version_table()
