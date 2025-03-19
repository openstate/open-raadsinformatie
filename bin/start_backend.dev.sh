#!/bin/sh

cd /opt/ori
find . -name "*.pyc" -exec rm -f {}
celery --app ocd_backend.app:celery_app flower &
#celery --app=ocd_backend.app:celery_app worker --pidfile=/var/run/celery/%n.pid --loglevel=info --concurrency=8
# nov 2024: using this now to start celery in development to get the logs. The "celery multi" command below may be faster
# but for some reason does not write to the logs
celery --app=ocd_backend.app:celery_app --quiet worker --loglevel=debug -Q transformers,enrichers --concurrency=8 --max-tasks-per-child=5 --without-gossip >> /opt/ori/data/ori.log 2>&1
# celery -A ocd_backend.app:celery_app multi start 4 -Q transformers,enrichers -c8 -l debug --pidfile=/var/run/celery/%n.pid
# while true
#   do
#     inotifywait -e modify,attrib,close_write,move,delete -r /opt/ori/ocd_backend \
#       && date \
#       && celery -A ocd_backend.app:celery_app multi restart 4 -Q transformers,enrichers -c8 -l debug --pidfile=/var/run/celery/%n.pid
#     sleep 10
#   done
