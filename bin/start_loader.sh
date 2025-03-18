#!/bin/sh

cd /opt/ori
celery --app=ocd_backend.app:celery_app --quiet worker --loglevel=info -Q loaders --concurrency=1 --without-gossip >> /opt/ori/data/ori.log 2>&1
