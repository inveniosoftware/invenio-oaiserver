..
    This file is part of Invenio.
    Copyright (C) 2016-2022 CERN.
    Copyright (C) 2024 Graz University of Technology.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version v3.2.0 (released 2025-03-26)

- component_templates: Allow the usage of component templates to define the record schemas

Version v3.1.0 (released 2024-12-16)

- percolator: use `OAISERVER_RECORD_INDEX` to determine percolator index
    * Instead of relying on the default `RecordIndexer` class to determine
      the percolator index, we reuse the `OAISERVER_RECORD_INDEX` config variable.

Version 3.0.0 (release 2024-12-06)

- fix: tests, apply invenio-indexer change
- fix: docs reference target not found
- tests: apply changes for sqlalchemy>=2.0
- setup: change to reusable workflows
- setup: bump major dependencies
- ci: fix docker compose call

Version v2.2.3 (released 2024-09-25)

- percolator: allow lazy strings from config for deletions

Version v2.2.2 (released 2024-09-11)

- percolator: allow lazy strings from config

Version 2.2.1 (released 2023-11-09)

- verbs: fix `from` parameter

Version 2.2.0 (released 2023-03-02)

- remove deprecated flask-babelex dependency and imports
- upgrade invenio_i18n

Version 2.1.1 (released 2022-11-29)

- Add translations

Version 2.1.0 (released 2022-10-03)

- Add support to OpenSearch v2
- Remove `doc_type` using search APIs

Version 2.0.1 (released 2022-09-27)

- Bump invenio-records
- Remove invenio-marc21 from tests

Version 2.0.0 (released 2022-09-25)

- Add support to OpenSearch
- Drop support to Elasticsearch < 7
- Upper pin Invenio dependencies
- Breaking: rename kwargs `document_es_ids` to `document_search_ids` and
  `document_es_indices` to `document_search_indices` in funcs
  `create_percolate_query` and `percolate_query`

Version 1.5.0 (released 2022-09-21)

- Adds system created flag field to oai-pmh set model
  to mark auto created sets

Version 1.4.2 (released 2022-05-23)

- Adds support for Flask v2.1

Version 1.4.1 (released 2022-03-01)

- Fixes marshmallow deprecation warning.

Version 1.4.0 (released 2022-02-22)

- OAI-PMH sets reimplementation via percolator queries during result fetching.
- Removes Python 2.7 support.
- Resumption token argument fixes.

Version 1.3.0 (released 2021-10-20)

- Unpin Flask version.

Version 1.2.2 (released 2021-09-17)

- Adds support for more easily integrating the OAI-PMH server in InvenioRDM.

- Adds new configuration variables for dependency injection of search class,
  ID fetcher, record getter tec.

- The release is fully backward compatibility and does not change any
  behaviour.

- Fixes a bug with Elasticsearch 7 causing invalid OAI-PMH output for the
  resumption token.

Version 1.2.1 (released 2021-07-12)

- Adds german translations

Version 1.2.0 (released 2020-03-17)

- Removes support for python 2.7
- Centralises management of Flask dependency via invenio-base

Version 1.1.2 (released 2019-07-19)

- fixes default config OAISERVER_QUERY_PARSER_FIELDS
- changes celery support module to invenio-celery

Version 1.1.1 (released 2019-07-31)

- Added support for Marshmallow v2 and v3.

Version 1.1.0 (released 2019-07-31)

- Added support for Eleasticsearch v7

Version 1.0.3 (released 2019-02-15)

- Pins marshmallow package to <3 in preparation for upcoming v3.0.0 release
  which will break compatibility.

Version 1.0.2 (released 2019-01-10)

- Improved performance of the *Identify* verb response by fetching earliest
  record date from Elasticsearch.

Version 1.0.1 (released 2018-12-14)

Version 1.0.0 (released 2018-03-23)

- Initial public release.
