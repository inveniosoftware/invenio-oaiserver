# SPDX-FileCopyrightText: 2016-2022 CERN.
# SPDX-FileCopyrightText: 2022 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Record field function."""

from .percolator import _delete_percolator, _new_percolator


def after_insert_oai_set(mapper, connection, target):
    """Update records on OAISet insertion."""
    _new_percolator(spec=target.spec, search_pattern=target.search_pattern)


def after_update_oai_set(mapper, connection, target):
    """Update records on OAISet update."""
    _delete_percolator(spec=target.spec, search_pattern=target.search_pattern)
    _new_percolator(spec=target.spec, search_pattern=target.search_pattern)


def after_delete_oai_set(mapper, connection, target):
    """Update records on OAISet deletion."""
    _delete_percolator(spec=target.spec, search_pattern=target.search_pattern)
