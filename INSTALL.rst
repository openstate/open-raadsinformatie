Open Raadsinformatie API install notes
######################################

.. contents::

Install using Docker
====================

Using `Docker <http://www.docker.com/>`_ is by far the easiest way to spin up a development environment and get started with contributing to the Open Raadsinformatie API. The following has been tested to work with Docker 17.06.0.

1. Clone the git repository::

   $ git clone https://github.com/openstate/open-raadsinformatie.git
   $ cd open-raadsinformatie/

2. Spin up all required containers, which are specified in the ``docker-compose.yml`` file. The required images will be automatically be pulled from `docker hub <https://hub.docker.com/u/openstatefoundation/>`_::

   $ docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

The backend container is responsible for extraction using the python Celery project. Mind that the Celery backend must be running before any items can be extracted.

It should take less than a minute to fire all containers up. It's recommended to include the ``docker-compose.dev.yml`` for local development, this will mount the local filesystem and enables local changes without having to rebuild the backend.
Now, instead of pulling for docker hub, the local tagged image will be used when restarting.

The following services are now accessible locally in the Docker container via ``http://127.0.0.1``, or from the host via ``http://<CONTAINER IP ADDRESS>`` (look up the container's IP address using ``docker inspect`` as shown below):

* Elasticsearch (:9200)
* Celery Flower GUI (:5555)

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
=====

Some quick notes on how to use the Open Raadsinformatie API

Running an extractor
--------------------

When the containers are started as described above, we can run an extraction. In another terminal run the following commands for extraction:

All sources can be shown by running::

   $ docker exec -it ori_backend_1 ./manage.py extract list_sources

Currently, there are new new-style YAML and old-style JSON sources, as explained below.
The extraction of new-style sources are started like this, with optional flags::

   $ docker exec -it ocd_backend_1 ./manage.py extract start <source_name> -s <subsource> -e <entity>
   $ docker exec -it ocd_backend_1 ./manage.py extract start ibabs -s amstelveen -e meetings

If the ``-s`` flag is not specified, all subsources will be processed one by one.
When the ``-e`` flag is not specified, all available entities for that subsource will be processed.

Old-style sources are started a bit different::

   $ docker exec -it ocd_backend_1 ./manage.py extract start <source_name>_<entity>

Understanding sources and entities
----------------------------------

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
