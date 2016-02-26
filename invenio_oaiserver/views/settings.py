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

"""OAI-PMH 2.0 server."""

from __future__ import absolute_import

from flask import Blueprint, flash, redirect, render_template, request, url_for
from invenio_db import db

from invenio_oaiserver.models import OAISet
from invenio_oaiserver.forms import OAISetForm

blueprint = Blueprint(
    'oaiserver_settings',
    __name__,
    url_prefix='/settings/oaiserver',
    static_folder='../static',
    template_folder='../templates/invenio_oaiserver/settings/',
)


@blueprint.route('/')
def index():
    """Index."""
    sets = OAISet.query.filter()
    return render_template('index.html', sets=sets)


@blueprint.route('/set/new')
def new_set():
    """Manage sets."""
    return render_template('make_set.html',
                           form=OAISetForm(),
                           action_url=url_for(".submit_set"),
                           action="Create new set")


@blueprint.route('/set/edit/<spec>')
def edit_set(spec):
    """Manage sets."""
    set_to_edit = OAISet.query.filter(OAISet.spec == spec).one()
    return render_template('make_set.html',
                           form=OAISetForm(obj=set_to_edit),
                           action="Edit {0}".format(spec),
                           action_url=url_for(".submit_edit_set", spec=spec))


@blueprint.route('/set/new', methods=['POST'])
def submit_set():
    """Insert a new set."""
    form = OAISetForm(request.form)
    if request.method == 'POST' and form.validate():
        new_set = OAISet(spec=form.spec.data,
                         name=form.name.data,
                         description=form.description.data,
                         search_pattern=form.search_pattern.data)
        db.session.add(new_set)
        db.session.commit()
        flash('New set {0} was created.'.format(new_set.spec))
        return redirect(url_for('.index'))
    return render_template('make_set.html', form=form, action="Create new set")


@blueprint.route('/set/edit/<spec>', methods=['POST'])
def submit_edit_set(spec):
    """Insert a new set."""
    form = OAISetForm(request.form)
    if request.method == 'POST' and form.validate():
        oaiset = OAISet.query.filter(OAISet.spec == str(spec)).one()
        oaiset.spec = form.spec.data
        oaiset.name = form.name.data
        oaiset.description = form.description.data
        oaiset.search_pattern = form.search_pattern.data
        db.session.add(oaiset)
        db.session.commit()
        flash('Set {0} was updated'.format(oaiset.spec))
        return redirect(url_for('.index'))
    return render_template('make_set.html',
                           form=form,
                           action="Edit {0}".format(spec))


# @blueprint.route('/set/delete/<spec>')
# def delete_set(spec):
#     """Manage sets."""
#     # SetRecord.query.filter(SetRecord.set_spec==spec).delete()
#     OAISet.query.filter(OAISet.spec == spec).delete()
#     db.session.commit()
#     flash('Set %s was deleted.' % spec)
#     return redirect(url_for('.index'))
