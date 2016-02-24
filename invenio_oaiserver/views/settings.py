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
from invenio_search import Query, current_search_client

from invenio_oaiserver.models import OAISet
from invenio_oaiserver.provider import OAIIDProvider
from invenio_oaiserver.views.forms.new_set import get_NewSetForm

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
    return render_template('make_set.html', new_set_form=get_NewSetForm())


@blueprint.route('/set/edit/<spec>')
def edit_set(spec):
    """Manage sets."""
    set_to_edit = OAISet.query.filter(OAISet.spec == spec).one()
    return render_template('edit_set.html',
                           edit_set_form=get_NewSetForm(obj=set_to_edit))


@blueprint.route('/set/new', methods=['POST'])
def submit_set():
    """Insert a new set."""
    form = get_NewSetForm(request.form)
    if request.method == 'POST' and form.validate():
        new_set = OAISet(spec=form.spec.data,
                         name=form.name.data,
                         description=form.description.data,
                         search_pattern=form.search_pattern.data)
        db.session.add(new_set)

        # this shoul be moved to UPDATER (celery task) and it sould always
        # take care of adding records to sets.
        ##########
        # query = Query(form.query.data)
        # response = current_search_client.search(
        #     index='records',  # make configurable PER SET
        #     doc_type='record',  # make configurable PER SET
        #     body=query.body,
        #     fields='_id, oaiid'  # path to oaiid as a configurable
        # )
        # ids = [(a['_id'], a['oaiid']) for a in response['hits']['hits']]
        # add_records_to_set(ids)
        #########

        db.session.commit()
        flash('New set %s was added.' % (new_set.spec,))
        return redirect(url_for('.index'))
    return render_template('make_set.html', new_set_form=form)


@blueprint.route('/set/edit/<spec>', methods=['POST'])
def submit_edit_set(spec):
    """Insert a new set."""
    form = get_NewSetForm(request.form)
    if request.method == 'POST' and form.validate():
        old_set = OAISet.query.filter(spec=spec)
        query = Query(old_set.search_pattern)
        old_recid = current_search_client.search(
            index='records',
            doc_type='record',
            body=query.body,
            fields='_id, oaiid'
        )
        query = Query(form.search_pattern)
        new_recid = current_search_client.search(
            index='records',
            doc_type='record',
            body=query.body,
            fields='_id, oaiid'
        )
        recids_to_delete = set(old_recid) - set(new_recid)
        # TODO: marks records as deleted from set
        remove_recids_from_set(recids_to_delete)
        add_records_to_set(new_recid)
        flash('Set was changed')
        return redirect(url_for('.manage_sets'))
    return render_template('edit_set.html', edit_set_form=form, spec=spec)


def add_records_to_set(ids):
    """Add records to set."""
    # use invenio-record functions to add set information to the record
    # get record via invenio-record.api.Record.... get_record
    for recid, oaiid in ids:
        if oaiid:
            # how to get and modify record
            rec = get_record(recid)
            rec['_oai'].append(new_set.name)
        else:
            # use minter for this
            oaiid = OAIIDProvider.create('rec', recid)
            rec = get_record(recid)
            # append set nam to the record (with append date as a separete
            # field) this needs to be configurable
            rec['_oai'].append(new_set.name)
        # new_set_record = SetRecord(set_spec=form.spec.data,
        #                            recid=recid)
        # db.session.add(new_set_record)

# @blueprint.route('/set/<str:name>', methods=['DELETE'])
# TODO: what happens when we delete a set


@blueprint.route('/set/delete/<spec>')
def delete_set(spec):
    """Manage sets."""
    # SetRecord.query.filter(SetRecord.set_spec==spec).delete()
    OAISet.query.filter(OAISet.spec == spec).delete()
    db.session.commit()
    flash('Set %s was deleted.' % spec)
    return redirect(url_for('.manage_sets'))
