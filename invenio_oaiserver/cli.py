# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016, 2017 CERN.
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

"""CLI for OAI Server."""

from __future__ import absolute_import, print_function

import click
from flask import current_app
from flask.cli import with_appcontext

from .tasks import update_affected_records


def abort_if_false(ctx, param, value):
    """Abort command is value is False."""
    if not value:
        ctx.abort()


@click.group()
def oaipmh():
    """Manage OAI PMH server."""


@oaipmh.command()
@click.option('--spec', '-s', default=None,
              help='Select records with OAI set.')
@click.option('--search-pattern', '-p', default=None,
              help='Select records by search pattern.')
@click.option('--delayed', '-d', is_flag=True,
              help='Run OAI set update in background.')
@click.option('--yes-i-know', is_flag=True, callback=abort_if_false,
              expose_value=False,
              prompt='Do you really want to update all matching records?')
@with_appcontext
def update(spec, search_pattern, delayed):
    """Run bulk record indexing."""
    if spec is None and search_pattern is None:
        search_pattern = ''

    if delayed:
        click.secho('Starting task updating records...', fg='green')
        update_affected_records.delay(spec=spec, search_pattern=search_pattern)
    else:
        click.secho('Updating records...', fg='green')
        update_affected_records(spec=spec, search_pattern=search_pattern)
