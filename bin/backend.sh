#!/bin/sh

cd /opt/ori
find . -name "*.pyc" -exec rm -f {}
celery flower --app=ocd_backend.app:celery_app &
#celery worker --app=ocd_backend.app:celery_app --attach --pidfile=/var/run/celery/%n.pid --loglevel=info --concurrency=8
# nov 2024: using this now to start celery in development to get the logs. The "celery multi" command below may be faster
# but for some reason does not write to the logs
celery --app=ocd_backend.app:celery_app worker --loglevel=debug -Q transformers,enrichers --concurrency=8 --without-gossip --quiet
# celery multi start 4 -Q transformers,enrichers -c8 -A ocd_backend.app:celery_app -l debug --pidfile=/var/run/celery/%n.pid
# while true
#   do
#     inotifywait -e modify,attrib,close_write,move,delete -r /opt/ori/ocd_backend \
#       && date \
#       && celery multi restart 4 -Q transformers,enrichers -c8 -A ocd_backend.app:celery_app -l debug --pidfile=/var/run/celery/%n.pid
#     sleep 10
#   done
