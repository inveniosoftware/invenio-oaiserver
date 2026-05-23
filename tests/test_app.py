# SPDX-FileCopyrightText: 2015-2025 CERN.
# SPDX-License-Identifier: MIT

"""Test app."""

import pytest
from flask import Flask

from invenio_oaiserver import InvenioOAIServer


def test_version():
    """Test version import."""
    from invenio_oaiserver import __version__

    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    with pytest.warns(
        UserWarning, match="Please specify the OAISERVER_ID_PREFIX configuration"
    ):
        InvenioOAIServer(app)
