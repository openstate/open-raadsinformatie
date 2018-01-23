#!/bin/sh

# source /opt/bin/activate
cd /opt/ori

./manage.py extract start ibabs
./manage.py extract start go
./manage.py extract start notubiz

./manage.py extract start oude_ijsselstreek_committees
./manage.py extract start oude_ijsselstreek_popit_organizations
./manage.py extract start oude_ijsselstreek_popit_persons
./manage.py extract start oude_ijsselstreek_meetings
./manage.py extract start oude_ijsselstreek_reports
./manage.py extract start oude_ijsselstreek_resolutions

./manage.py extract start harderwijk_popit_organizations
./manage.py extract start harderwijk_popit_persons
./manage.py extract start harderwijk_videotulen
