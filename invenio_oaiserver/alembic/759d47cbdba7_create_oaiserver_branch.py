# SPDX-FileCopyrightText: 2016-2018 CERN.
# SPDX-License-Identifier: MIT

"""Create oaiserver branch."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "759d47cbdba7"
down_revision = None
branch_labels = ("invenio_oaiserver",)
depends_on = "dbdbc1b19cf2"


def upgrade():
    """Upgrade database."""
    pass


def downgrade():
    """Downgrade database."""
    pass
