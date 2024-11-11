#!/bin/sh

cd /opt/ori
find . -name "*.pyc" -exec rm -f {}
celery flower --app=ocd_backend.app:celery_app &
#celery worker --app=ocd_backend.app:celery_app --attach --pidfile=/var/run/celery/%n.pid --loglevel=info --concurrency=8
celery multi start 4 -Q transformers,enrichers -c8 -A ocd_backend.app:celery_app -l debug --logfile=log/celery.log --pidfile=/var/run/celery/%n.pid
while true
  do
    inotifywait -e modify,attrib,close_write,move,delete -r /opt/ori/ocd_backend \
      && date \
      && celery multi restart 4 -Q transformers,enrichers -c8 -A ocd_backend.app:celery_app -l debug --logfile=log/celery.log --pidfile=/var/run/celery/%n.pid
    sleep 10
  done
