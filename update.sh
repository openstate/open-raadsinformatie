#!/bin/bash

source /opt/bin/activate
./opt/npo/manage.py extract start npo_journalistiek
./opt/npo/manage.py extract start prid
./opt/npo/manage.py extract start metadata
./opt/npo/manage.py extract start tt888
