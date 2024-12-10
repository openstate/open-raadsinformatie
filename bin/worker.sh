#!/bin/sh
cd /opt/ori
celery -A ocd_backend.app:celery_app worker -l debug
