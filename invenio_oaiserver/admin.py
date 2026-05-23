# SPDX-FileCopyrightText: 2015-2025 CERN.
# SPDX-FileCopyrightText: 2024 KTH Royal Institute of Technology.
# SPDX-FileCopyrightText: 2026 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Admin model views for OAI sets."""

from flask_admin.contrib.sqla import ModelView
from invenio_admin.filters import FilterConverter
from invenio_i18n import gettext as _

from .models import OAISet


class OAISetModelView(ModelView):
    """OAISets model view."""

    filter_converter = FilterConverter()

    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True
    column_list = (
        "id",
        "spec",
        "name",
        "updated",
        "created",
    )
    column_details_list = (
        "id",
        "spec",
        "name",
        "description",
        "search_pattern",
        "updated",
        "created",
    )
    column_filters = ("name", "created", "updated")
    column_default_sort = ("updated", True)
    column_searchable_list = ["spec", "name", "description"]
    page_size = 25

    def edit_form(self, obj):
        """Customize edit form."""
        form = super(OAISetModelView, self).edit_form(obj)
        del form.spec
        return form


set_adminview = dict(
    modelview=OAISetModelView,
    model=OAISet,
    category=_("OAI-PMH"),
    name=_("Sets"),
)
