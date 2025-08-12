#!/bin/bash
FQPATH=`readlink -f $0`
BINDIR=`dirname $FQPATH`
TODAY=`date +%Y-%m-%d`
DAY_BEFORE_YESTERDAY=`date -d "-4 day" +%Y-%m-%d` # 4 to catch documents since last reindex; change back to 2 after a few days
cd $BINDIR/..
sudo docker exec ori_redis_1 redis-cli --scan --pattern 'pipeline_*' |sudo xargs docker exec ori_redis_1 redis-cli del
sudo docker exec ori_redis_1 redis-cli -n 1 set _daily.start_date "$DAY_BEFORE_YESTERDAY"
sudo docker exec ori_redis_1 redis-cli -n 1 set _daily.end_date "$TODAY"
sudo docker exec ori_backend_1 ./manage.py extract load_redis 'all daily monthly'
sudo docker exec ori_backend_1 ./manage.py extract list_sources |tail -n +2 |grep ' -s '|sed 's/ - //' |sed 's/ -s /./' >sources.txt
#sudo docker exec ori_backend_1 ./manage.py extract process daily
