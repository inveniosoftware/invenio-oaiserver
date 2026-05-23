# SPDX-FileCopyrightText: 2022 CERN.
# SPDX-License-Identifier: MIT

"""Add system_created field."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "5d25c1981985"
down_revision = "e655021de0de"
branch_labels = ()
depends_on = None


def upgrade():
    """Upgrade database."""
    op.add_column(
        "oaiserver_set",
        sa.Column(
            "system_created",
            sa.Boolean(),
            default=False,
            server_default=sa.sql.expression.literal(False),
            nullable=False,
        ),
    )


def downgrade():
    """Downgrade database."""
    op.drop_column("oaiserver_set", "system_created")
