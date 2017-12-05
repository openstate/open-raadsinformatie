#!/bin/sh

source /opt/bin/activate
cd /opt/ori

./manage.py extract start ibabs -s amstelveen
./manage.py extract start ibabs -s heerde
./manage.py extract start ibabs -s utrecht
./manage.py extract start ibabs -s enschede
./manage.py extract start ibabs -s gouda
./manage.py extract start ibabs -s overbetuwe
./manage.py extract start ibabs -s medemblik
./manage.py extract start ibabs -s oss
./manage.py extract start ibabs -s zoetermeer

./manage.py extract start go -s goirle
./manage.py extract start go -s den_helder
./manage.py extract start go -s doetinchem
./manage.py extract start go -s noordoostpolder
./manage.py extract start go -s steenbergen

./manage.py extract start oude_ijsselstreek_committees
./manage.py extract start oude_ijsselstreek_popit_organizations
./manage.py extract start oude_ijsselstreek_popit_persons
./manage.py extract start oude_ijsselstreek_meetings
./manage.py extract start oude_ijsselstreek_reports
./manage.py extract start oude_ijsselstreek_resolutions

./manage.py extract start harderwijk_popit_organizations
./manage.py extract start harderwijk_popit_persons
./manage.py extract start harderwijk_videotulen
