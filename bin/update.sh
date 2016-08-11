#!/bin/sh

source /opt/bin/activate
cd /opt/ori

# first only do ibabs to popit update
for JSON_FILE in ocd_backend/sources/*.json
do
  MUNI=`basename $JSON_FILE .json`
  # utrecht_ibabs_most_recent_popit_persons
  UPDATABLE_SOURCES="${MUNI}_ibabs_most_recent_popit_persons ${MUNI}_ibabs_most_recent_popit_organizations ${MUNI}_ibabs_most_recent_popit_memberships ${MUNI}_ibabs_most_recent_popit_council_memberships"

  for UPDATE_SOURCE in $UPDATABLE_SOURCES
  do
    echo `date` $UPDATE_SOURCE
    ./manage.py extract start $UPDATE_SOURCE --sources_config=$JSON_FILE
    sleep 60
  done

  sleep 60
done

# now do the other updates as well
for JSON_FILE in ocd_backend/sources/*.json
do
  MUNI=`basename $JSON_FILE .json`
  UPDATABLE_SOURCES="${MUNI}_committees ${MUNI}_popit_organizations ${MUNI}_popit_persons ${MUNI}_meetings ${MUNI}_reports ${MUNI}_resolutions ${MUNI}_videotulen ${MUNI}_motions ${MUNI}_vote_events ${MUNI}_voting_rounds ${MUNI}_meeting_attendees"

  for UPDATE_SOURCE in $UPDATABLE_SOURCES
  do
    echo `date` $UPDATE_SOURCE
    ./manage.py extract start $UPDATE_SOURCE --sources_config=$JSON_FILE
    sleep 60
  done

  sleep 60
done
echo `date` "All done"
