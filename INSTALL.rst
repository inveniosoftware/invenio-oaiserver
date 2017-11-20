Installation
============

Invenio-OAIServer is on PyPI so all you need is:

.. code-block:: console

   $ pip install invenio-oaiserver

Invenio-OAIServer depends on Invenio-Search, Invenio-Records and Celery/Kombu.

**Requirements**

Invenio-OAIServer requires a message queue in addition to Elasticsearch (Invenio-Search) and a database (Invenio-Records). See Kombu documentation for list of supported message queues (e.g. RabbitMQ): http://kombu.readthedocs.io/en/latest/introduction.html#transport-comparison
