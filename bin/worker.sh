#!/bin/sh
cd /opt/ori
celery worker -A ocd_backend:celery_app -l debug
