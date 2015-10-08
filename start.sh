#!/bin/bash

source /opt/bin/activate

cd /opt/ori

service elasticsearch restart
service redis restart

sleep 20

supervisord -n -c conf/supervisor.conf
