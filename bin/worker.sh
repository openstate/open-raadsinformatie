#!/bin/sh
cd /opt/ori
celery worker -A ocd_backend.app:celery_app -l debug
