#!/bin/sh

# source /opt/bin/activate
cd /opt/ori

./manage.py extract list_sources |awk 'NR > 1 {print $0}' |grep '\-s' |grep -v archive |grep -v 'zuid-holland' |cut -c 4- >.commands

while IFS='' read -r line || [[ -n "$line" ]]; do
    ./manage.py extract start $line
    sleep 60
done <.commands

# ./manage.py extract start ibabs
# ./manage.py extract start go
# ./manage.py extract start notubiz
# ./manage.py extract start parlaeus
#
./manage.py extract start oude_ijsselstreek_committees
./manage.py extract start oude_ijsselstreek_popit_organizations
./manage.py extract start oude_ijsselstreek_popit_persons
./manage.py extract start oude_ijsselstreek_meetings
./manage.py extract start oude_ijsselstreek_reports
./manage.py extract start oude_ijsselstreek_resolutions

./manage.py extract start harderwijk_popit_organizations
./manage.py extract start harderwijk_popit_persons
./manage.py extract start harderwijk_videotulen
#
# ./manage.py extract start go-provinces
# ./manage.py extract start ibabs-provinces
