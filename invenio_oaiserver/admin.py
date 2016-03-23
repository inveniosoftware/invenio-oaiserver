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

"""Admin model views for OAI sets."""

from flask_admin.contrib.sqla import ModelView

from .models import OAISet


def _(x):
    """Identity."""
    return x


class OAISetModelView(ModelView):
    """OAISets model view."""

    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True
    column_list = ('id', 'spec', 'updated', 'created',)
    column_details_list = ('id', 'spec', 'name', 'description',
                           'search_pattern', 'updated', 'created')
    column_filters = ('created', 'updated')
    column_default_sort = ('updated', True)
    page_size = 25

    def edit_form(self, obj):
        """Customize edit form."""
        form = super(OAISetModelView, self).edit_form(obj)
        del form.spec
        return form

set_adminview = dict(
    modelview=OAISetModelView,
    model=OAISet,
    category=_('OAI-PMH'),
    name=_('Sets'),
)
