#!/bin/sh
# Purges Postgres database, Redis and Elastic Search index.

if [ "$RELEASE_STAGE" != "development" ]; then
  echo "*** This should be run inside the backend Docker container ***"
  exit
fi

./manage.py developers purge_dbs