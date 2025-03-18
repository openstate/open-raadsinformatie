#!/bin/sh
# When concurrency was 14 machine nearly crashed due to memory full and swap space full
cd /opt/ori
celery --app=ocd_backend.app:celery_app --quiet worker --loglevel=info -Q transformers,enrichers --concurrency=7 --without-gossip >> /opt/ori/data/ori.log 2>&1
