#!/bin/sh

cd /opt/ori
celery --app=ocd_backend.app:celery_app --quiet worker --loglevel=info -Q transformers,enrichers --concurrency=14 --without-gossip >> /opt/ori/data/ori.log 2>&1
