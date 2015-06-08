Open Raadsinformatie API install notes
######################################

.. contents::

Installation instructions
=============

Install either using Docker, Vagrant or manually.

Install using Docker
------------

Using `Docker <http://www.docker.com/>`_ is by far the easiest way to spin up a development environment and get started with contributing to the NPO Backstage API. The following has been tested to work with Docker 1.0.1 and up.

1. Clone the NPO Backstage git repository::

   $ git clone https://github.com/openstate/open-raadsinformatie.git
   $ cd open-raadsinformatie/

2. Build an image using the Dockerfile, i.e. use Ubuntu as base and install all dependencies, and call it open-state/open-raadsinformatie::

   $ docker build -t open-state/open-raadsinformatie .

3. Create a container based on the newly created open-state/open-raadsinformatie image. The current folder on the host machine (which should be the root of theopen-raadsinformatie repo!) is mounted on /opt/npo in the container (so you can just develop on your host machine using your favorite development setup). Furthermore port 9200 is mapped from the container to the host machine so you can reach elasticsearch on http://127.0.0.1:9200, the same holds for port 5000 which gives access to the API::

   $ docker run -it --name c-open-raadsinformatie -v `pwd`:/opt/ori -p 9200:9200 -p 5000:5000 open-state/open-raadsinformatie

4. Once connected to the container the following commands currently still have to be executed manually::

   $ service elasticsearch restart
   $ redis-server &

Elasticsearch is now accessible locally in the Docker container via http://127.0.0.1:9200, or from the host via http://<CONTAINER IP ADDRESS>:9200 (look up the container's IP address using ``docker inspect`` as shown below).

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

Install using Vagrant
------------

It is also possible to use `Vagrant <http://www.vagrantup.com/>`_  to install the NPO Backstage API.

1. Clone the NPO Backstage git repository::

   $ git clone https://github.com/openstate/npo-backstage.git
   $ cd npo-backstage/

2. Select and link the correct ``Vagrantfile`` (depending on the Vagrant provider you use; in this case virtualbox)::

   $ ln -s Vagrantfile.virtualbox Vagrantfile

3. Start the Vagrant box and SSH into it::

   $ vagrant up && vagrant ssh

Vagrant will automatically sync your project directory (the directory with the Vagrantfile) between the host and guest machine. Also, it will run a bootstrap script that will take care of installing project dependencies. In vagrant machine, the project directory can be found under ``/vagrant``. For more information, see the Vagrant documentation on `Synced Folders <http://docs.vagrantup.com/v2/synced-folders/index.html>`_.

Install manually on Ubuntu
------------

Prerequisites
~~~~~~~~~~~~

- Redis
- Elasticsearch >= 1.1
- Python(-dev) 2.7
- liblxml
- libxslt
- pip
- virtualenv (optional)

Installation
~~~~~~~~~~~~

Create or go to the directory where you want to place the NPO Backstage files.

1. Install Redis::

   $ sudo add-apt-repository ppa:rwky/redis
   $ sudo apt-get update
   $ sudo apt-get install redis-server

2. Install Java (if it isn't already)::

   $ sudo apt-get install openjdk-7-jre-headless

3. Install Elasticsearch and the head plugin::

   $ wget https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.4.2.deb
   $ sudo dpkg -i elasticsearch-1.4.2.deb
   $ sudo service elasticsearch start
   $ sudo /usr/share/elasticsearch/bin/plugin --install mobz/elasticsearch-head

4. Install other packages::

   $ sudo apt-get install -y make libxml2-dev libxslt1-dev libssl-dev libffi-dev libtiff4-dev libjpeg8-dev liblcms2-dev python-software-properties python-dev python-setuptools python-virtualenv git
   $ sudo easy_install pip

5. Clone the NPO Backstage git repository::

   $ git clone https://github.com/openstate/npo-backstage.git
   $ cd npo-backstage/

6. Compile dependencies for pyav::
   $ sudo ./install_pyav_deps.sh

7. (optional) Create a NPO Backstage virtualenv and source it (don't forget to source the virtualenv every time you start developing)::
   $ cd ..
   $ virtualenv npo
   $ source npo/bin/activate
   $ cd npo-backstage

8. Install Python requirements::

   $ pip install Cython==0.21.2 && pip install -r requirements.txt

8. Initialize the Elasticsearch instance::

   $ ./manage.py elasticsearch create_indexes es_mappings
   $ ./manage.py elasticsearch put_template

Usage
============

Some quick notes on how to use the NPO Backstage API

Running an NPO Backstage extractor
------------

1. Make the necessary changes to the 'sources' settings file (``ocd_backend/sources.json``). For example, fill out any API keys you might need for specific APIs.

2. Start worker processes::

   $ celery --app=ocd_backend:celery_app worker --loglevel=info --concurrency=2

3. In another terminal (in case of Docker, use ``docker exec`` as described above), start the extraction process::

   $ ./manage.py extract start npo_journalistiek

   You can get an overview of the available sources by running ``./manage.py extract list_sources``.

Running the API frontend
------------

Once started, the API can be accessed on port 5000 (again either locally or from the host, similar to accessing elasticsearch as described above)::

   $ ./manage.py frontend runserver

Automatic updating using cron
------------

The ``update.sh`` script contains the instructions to update indices. In the case of docker it is the easiest to add this script to the crontab on the host machine. Using ``sudo crontab -e``, add the following line when using ``docker-enter``::

   $ 0 1,7,13,19 * * * sudo docker-enter c-npo-backstage ./opt/npo/update.sh

Or the following line if your docker version has the ``exec`` command::

   $ 0 1,7,13,19 * * * sudo docker exec c-npo-backstage ./opt/npo/update.sh
