# SPDX-FileCopyrightText: 2016-2022 CERN.
# SPDX-FileCopyrightText: 2022 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Error."""


class OAIBadMetadataFormatError(Exception):
    """Metadata format required doesn't exist."""


class OAISetSpecUpdateError(Exception):
    """Spec attribute cannot be updated.

    The correct way is to delete the set and create a new one.
    """


class OAINoRecordsMatchError(Exception):
    """No records match the query.

    The combination of the values of the from, until, and set arguments
    results in an empty list.
    """
