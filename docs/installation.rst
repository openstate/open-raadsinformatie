Open Raadsinformatie API installation and usage
###############################################

.. contents::

Install using Docker
====================

Using `Docker <http://www.docker.com/>`_ is by far the easiest way to spin up a development environment and get started
with contributing to the Open Raadsinformatie project. The following has been tested to work with Docker 18.09.7 .

1. Clone the git repository::

   $ git clone https://github.com/openstate/open-raadsinformatie.git
   $ cd open-raadsinformatie/

2. Use `Docker Compose <https://docs.docker.com/compose/>`_ to spin up all required containers, which are specified in
the ``docker-compose.yml`` file. The required images will automatically be pulled from
`docker hub <https://hub.docker.com/u/openstatefoundation/>`_::

   $ docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

The first time you run this command it may take about 10 to 15 minutes to pull and build all images. After that it
should take less than a minute to fire up all containers. Including ``docker-compose.dev.yml`` will mount the local
filesystem into the ``backend`` container and enables making local changes without having to rebuild the image after
every change.

The following services are now accessible locally in the Docker container via ``http://127.0.0.1``, or from the host
via ``http://<CONTAINER IP ADDRESS>`` (look up the container's IP address using ``docker inspect`` as shown below):

* Elasticsearch (:9200)
* Celery Flower GUI (:5555)
* PgAdmin (:8081)

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

First-time setup
================

Before you can start developing you will need to run the following steps:

1. Create a virtual environment and install the requirements in ``ocd_backend/requirements.txt``.

2. The Postgres database needs to be created before it can be used::

    docker exec -it -u postgres ori_postgres_1 psql

    CREATE DATABASE ori;
    CREATE USER ori_postgres_user WITH PASSWORD 'XXX';
    GRANT ALL PRIVILEGES ON DATABASE ori TO ori_postgres_user;

3. If you wish to use the Google Cloud Storage features such as caching you will need to download the JSON file with
your credentials and have it available locally to be loaded as an environment variable (see Usage).

4. Create a ``local_settings.py`` file in ``/ocd_backend`` with the following contents::

    import settings

    try:
        settings.REDIS_HOST = 'localhost'
        settings.REDIS_PORT = 6380
        settings.CELERY_CONFIG['BROKER_URL'] = 'redis://localhost:6380/0'
        settings.CELERY_CONFIG[
            'CELERY_RESULT_BACKEND'] = 'ocd_backend.result_backends:OCDRedisBackend+redis://localhost:6380/0'
    except:
        pass

    settings.ELASTICSEARCH_HOST = 'localhost'
    settings.POSTGRES_HOST = 'localhost'
    settings.API_URL = 'http://localhost:5000/v1/'

This instructs the ``backend`` container to use a locally running instance of Redis, which makes it easier to inspect
and manipulate the task queue. It also makes the Elasticsearch endpoint available on ``localhost``.

Database migrations
===================

This project uses `Alembic <https://alembic.sqlalchemy.org/>`_ to manage database migrations. To migrate the database
to the current revision run the following command from the ``ocd_backend/alembic`` folder::

    alembic upgrade head

If you make changes that require a new database migration, you can create it by running the following command from
the ``ocd_backend/alembic`` folder::

    alembic revision --autogenerate -m 'message'

Alembic will attempt to automatically detect what changes you made and create a new revision file in
``ocd_backend/alembic/versions``. This process is far from fool-proof, so always go over this file manually and make
adjustments if needed.

After creating a revision, don't forget to run the ``alembic upgrade head`` command to apply it.

Usage
=====

To test the extraction process and resulting data during development, you will need to run the following steps.

Starting your development environment
-------------------------------------

1. Start the docker containers including ``docker-compose.dev.yml`` (see Install using Docker)

2. Run a local instance of Redis using the following command::

    docker run -p 6380:6379 --rm redis

If you want to interrupt the extraction process because it has crashed or because it is taking too long, simply
quit the container using CTRL+c and the task queue will be cleared. Because of the ``--rm`` parameter the task queue
will be empty each time you (re-)start Redis.

3. Run the Celery backend::

    celery --app=ocd_backend:celery_app worker --loglevel=info --concurrency=1

Note the log level: change this to ``debug`` if you want more debug information. If you want to use the Google Cloud
Storage features such as caching you will need to add an environment variable called ``GOOGLE_APPLICATION_CREDENTIALS``
that points to the JSON file with your credentials (see First-time setup).

Note that the Celery app needs to be restarted after you make local changes for the changes to take effect.

Running an extractor
--------------------

After setting up your environment you can run the following commands for extraction.

All sources can be shown by running::

   python manage.py extract list_sources

The extraction of sources is started like this, with optional flags::

   python manage.py extract start <source_name> -s <subsource> -e <entity>

For example, to extract only meetings from Amtelveen::

   python manage.py extract start ori.ibabs -s amstelveen -e meetings

If the ``-s`` flag is not specified, all subsources will be processed one by one. When the ``-e`` flag is not
specified, all available entities for that subsource will be processed.

Understanding sources and entities
----------------------------------

New sources can be added to ``ocd_backend/sources``. It's important to understand how YAML aliases and anchors work
to know how these YAML sources are expanded. Variables like ``{sitename}`` are substituted in Python for the
corresponding key.

Most sources have the following entities defined (but more entities can be defined per source):

* municipality or province
* committees
* organizations
* persons
* meetings
* reports
