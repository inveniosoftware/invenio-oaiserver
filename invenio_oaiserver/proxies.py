# SPDX-FileCopyrightText: 2016-2022 CERN.
# SPDX-License-Identifier: MIT

"""Helper proxy to the state object."""

from flask import current_app
from werkzeug.local import LocalProxy

current_oaiserver = LocalProxy(lambda: current_app.extensions["invenio-oaiserver"])
"""Helper proxy to access state object."""
