#!/bin/bash
FQPATH=`readlink -f $0`
BINDIR=`dirname $FQPATH`
TODAY=`date +%Y-%m-%d`
YESTERDAY=`date -d yesterday +%Y-%m-%d`
cd $BINDIR/..
sudo docker exec ori_redis_1 redis-cli -n 1 set _daily.start_date "$YESTERDAY"
sudo docker exec ori_redis_1 redis-cli -n 1 set _daily.end_date "$TODAY"
sudo docker exec ori_backend_1 ./manage.py extract load_redis 'all daily monthly'
sudo docker exec ori_backend_1 ./manage.py extract list_sources |tail -n +2 |grep ' -s ' |awk '{print $(NF)}' >sources.txt
#sudo docker exec ori_backend_1 ./manage.py extract process daily
