NPO Backstage API install notes
###################################

Using Docker
=============

Using `Docker <http://www.docker.com/>`_ is by far the easiest way to spin up a development environment and get started with contributing to the NPO Backstage API.

1. Clone the OCD git repository::

   $ git clone https://github.com/openstate/npo-backstage.git
   $ cd npo-backstage/

2. Build an image using the Dockerfile, i.e. use Ubuntu as base and install all dependencies, and call it open-state/npo-backstage::

   $ docker build -t open-state/npo-backstage .

3. Create a container based on the newly created open-state/npo-backstage image. The current folder on the host machine (which should be the root of the npo-backstage repo!) is mounted on /opt/npo in the container. Furthermore port 9200 is mapped from the container to the host machine so you can reach elasticsearch on http://127.0.0.1:9200::

   $ docker run -it -v `pwd`:/opt/npo -p 9200:9200 open-state/npo-backstage

Manual setup
============

Pre-requisites
--------------

- Redis
- Elasticsearch >= 1.1
- Python(-dev) 2.7
- liblxml
- libxslt
- pip
- virtualenv (optional)

Installation
------------

1. Install redis::

   $ sudo add-apt-repository ppa:rwky/redis
   $ sudo apt-get update
   $ sudo apt-get install redis-server
   
2. Install Java (if it isn't already)::
   
   $ sudo apt-get install openjdk-7-jre-headless

3. Install Elasticsearch::
   
   $ wget https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.4.2.deb
   $ sudo dpkg -i elasticsearch-1.4.2.deb

4. Install liblxml, libxslt, libssl, libffi and python-dev::

   $ sudo apt-get install libxml2-dev libxslt1-dev libssl-dev libffi-dev python-dev

5. Install pip and virtualenv::

   $ sudo easy_install pip

6. Create an NPO Backstage virtualenv and source it::

   $ virtualenv npo
   $ source npo/bin/activate

7. Clone the NPO Backstage git repository and install the required Python packages::

   $ git clone https://github.com/openstate/npo-backstage.git
   $ cd npo-backstage/
   $ pip install -r requirements.txt


Running an NPO Backstage extractor
========================

1. First, add the NPO Backstage template to the running Elasticsearch instance::

   $ ./manage.py elasticsearch put_template

2. Make the necessary changes to the 'sources' settings file (``ocd_backend/sources.json``). For example, fill out any API keys you might need for specific APIs.

3. Start the extraction process::

   $ ./manage.py extract start npo-journalistiek

   You can get an overview of the available sources by running ``./manage.py extract list_sources``.

4. Simultaneously start a worker processes::

   $ celery --app=ocd_backend:celery_app worker --loglevel=info --concurrency=2
