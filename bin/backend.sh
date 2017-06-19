#!/bin/sh

celery flower --app=ocd_backend:celery_app &
celery multi start 1 -A ocd_backend:celery_app -l info --logfile=log/celery.log -c8 --pidfile=/var/run/celery/%n.pid

while true
  do
    inotifywait -e modify,attrib,close_write,move,delete -r /opt/ori/ocd_backend && date && celery multi restart 1 -A ocd_backend:celery_app --logfile=log/celery.log --pidfile=/var/run/celery/%n.pid
    sleep 10
  done
