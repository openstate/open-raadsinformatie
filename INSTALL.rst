Open Raadsinformatie API install notes
######################################

.. contents::

Install using Docker
=============

Using `Docker <http://www.docker.com/>`_ is by far the easiest way to spin up a development environment and get started with contributing to the Open Raadsinformatie API. The following has been tested to work with Docker 17.06.0.

1. Clone the git repository::

   $ git clone https://github.com/openstate/open-raadsinformatie.git
   $ cd open-raadsinformatie/

2. Spin up all required containers, which are specified in the ``docker-compose.yml`` file. The required images will be automatically be pulled from `docker hub <https://hub.docker.com/u/openstatefoundation/>`_::

   $ docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

For running Elasticsearch make sure your ``vm.max_map_count=262144`` by running::

   $ sudo sysctl -w vm.max_map_count=262144

or setting this in ``/etc/sysctl.conf``, otherwise this will result in an error like ``max virtual memory areas vm.max_map_count [65530] likely too low, increase to at least [262144]``.

The backend container is responsible for extraction using the python Celery project. Mind that the Celery backend must be running before any items can be extracted.

It should take less than a minute to fire all containers up. It's recommended to include the ``docker-compose.dev.yml`` for local development, this will mount the local filesystem and enables local changes without having to rebuild the backend.

The frontend however still needs to be rebuild in order to see the changes::

   $ docker build ocd_frontend -t openstatefoundation/open-raadsinformatie-frontend

Now, instead of pulling for docker hub, the local tagged image will be used when restarting.

The following services are now accessible locally in the Docker container via ``http://127.0.0.1``, or from the host via ``http://<CONTAINER IP ADDRESS>`` (look up the container's IP address using ``docker inspect`` as shown below):

* Elasticsearch (:9200)
* Celery Flower GUI (:5555)
* ORI Frontend API (:5000)

Some useful Docker commands::

   # Show all docker images on your machine
   $ docker images

   # List all containers which are currently running
   $ docker ps

   # List all containers
   $ docker ps -a

   # Connect another shell to a currently running container (useful during development)
   $ docker exec -it <CONTAINER ID/NAME> bash

   # Start a stopped container and automatically attach to it (-a)
   $ docker start -a <CONTAINER ID/NAME>

   # Attach to a running container (use `exec` though if you want to open any extra shells beyond this one)
   $ docker attach <CONTAINER ID/NAME>

   # Return low-level information on a container or image (e.g., a container's IP address)
   $ docker inspect <CONTAINER/IMAGE ID/NAME>

   Also, if attached to a container, either via run, start -a or attach, you can detach by typing CTRL+p CTRL+q

Usage
============

Some quick notes on how to use the Open Raadsinformatie API

On a fresh Elasticsearch instance
------------

Put template and create indexes, so we don't get a ``KeyError: 'aggregations'`` (on ``/opt/ori/ocd_frontend/rest/views.py", line 259, in format_sources_results``) when querying ``/v0/sources``::

   $ docker exec -it ori_backend_1 ./manage.py elasticsearch put_template
   $ docker exec -it ori_backend_1 ./manage.py elasticsearch create_indexes es_mappings

Running an extractor
------------

When the containers are started as described above, we can run an extraction. In another terminal run the following commands for extraction:

All sources can be shown by running::

   $ docker exec -it ori_backend_1 ./manage.py extract list_sources

Currently, there are new new-style YAML and old-style JSON sources, as explained below.
The extraction of new-style sources are started like this, with optional flags::

   $ docker exec -it ori_backend_1 ./manage.py extract start <source_name> -s <subsource> -e <entity>
   $ docker exec -it ori_backend_1 ./manage.py extract start ibabs -s amstelveen -e meetings

If the ``-s`` flag is not specified, all subsources will be processed one by one.
When the ``-e`` flag is not specified, all available entities for that subsource will be processed.

Old-style sources are started a bit different::

   $ docker exec -it ori_backend_1 ./manage.py extract start <source_name>_<entity>

Understanding sources and entities
------------

New sources can be added to ``ocd_backend/sources`` in either the new-style YAML or the old-style JSON format.
It's important to understand how YAML aliases and anchors work to know how these YAML sources are expanded.
Variables like ``{sitename}`` are subsituted in python by the corresponding key.

Most sources have the following entities defined (but more entities can be defined per source):

* municipality
* committees
* organizations
* persons
* meetings
* reports

When running ``list_sources``, old sources are ending with an underscore and entity.
New-style sources containing subsources can be recognised by an ``-s``.

In order to link entities the project currently searches for existing entities in Elasticsearch.
Therefore the order as specified above must be maintained, an organization entity needs to be extracted *before* the meeting entity since the meeting refers to an organization, which would not yet been indexed.
This behaviour will change when Elasticsearch is replaced by Neo4j which is currently being developed.

Debugging
------------

In the ``log`` directory check the ``backend.log`` and ``celery.log`` files for log output. You can also check ``docker-compose logs``. Sometimes extractors can hang with a 'Waiting for last chain to finish' message in ``backend.log``, you can sometimes fix this by removing the compiled Python files by running ``find . -name "*.pyc" -exec rm -f {} \;``.

You can check the values in Redis as follows::

   $ docker exec -it ori_redis_1 sh
   $ redis-cli
   $ KEYS *

You can clear Redis by running::

   $ docker exec -it ori_redis_1 sh
   $ redis-cli
   $ FLUSHALL
