#!/bin/sh

cd /opt/ori

SOURCES="ocd_backend/sources/$1.json"

UPDATABLE_SOURCES="$1_committees $1_popit_organizations $1_popit_persons $1_meetings $1_reports $1_resolutions"

for UPDATE_SOURCE in $UPDATABLE_SOURCES
do
  echo $UPDATE_SOURCE
  ./manage.py extract start $UPDATE_SOURCE --sources_config=$SOURCES
done
