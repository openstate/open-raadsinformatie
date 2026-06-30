#!/bin/bash
FQPATH=`readlink -f $0`
BINDIR=`dirname $FQPATH`
TODAY=`date +%Y-%m-%d`
END_DATE=`date -d "+3 month" +%Y-%m-%d`
cd $BINDIR/..
sudo docker exec ori_backend_1 ./manage.py extract synced_process all --start_date=$TODAY --end_date=$END_DATE --spotlight
