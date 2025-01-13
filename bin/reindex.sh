#!/bin/bash
# This script will reindex all municipalities listed in $TO_INDEX_FILENAME. It is
# run periodically by crontab to see if the next municipality can be started.
# It will only start the next municipality if the lock has been released for the previous.
# If too much time elapses before the lock is released, a mail is sent to warn about potential problems (TODO)
# Start and end times of processing are written to $INDEXED_FILENAME.
# If you want this script not to pick up the next municipality after the current one finishes, do a
#       touch maintenance.txt
SUDO="sudo " # In development substitute with empty string
MAINTENANCE_FILE="maintenance.txt"
LOCK_KEY="ori_lock_key"
LOCK_TIME_KEY="ori_lock_time_key"
IS_LOCKED="ori_is_locked"

TO_INDEX_FILENAME='to_index.txt'
INDEXED_FILENAME='indexed.log'
START_DATE='2010-01-01'
END_DATE=`date -d "-1 day" +%Y-%m-%d`
INDEXING_TIME_LIMIT=400 # seconds

FQPATH=`readlink -f $0`
BINDIR=`dirname $FQPATH`
HOMEDIR=`dirname $BINDIR`
cd $HOMEDIR

if test -f "$HOMEDIR/$MAINTENANCE_FILE"; then
    echo "Maintenance, bailing out"
    exit
fi

function check_locked() {
    local lock_value=$($SUDO docker exec ori_redis_1 sh -c "redis-cli -n 1 get $LOCK_KEY")
    if [ -n "$lock_value" ]; then
        echo $IS_LOCKED
    fi
}

function set_lock() {
    local source=$1
    $SUDO docker exec ori_redis_1 sh -c "redis-cli -n 1 set $LOCK_KEY $source"
    $SUDO docker exec ori_redis_1 sh -c "redis-cli -n 1 set $LOCK_TIME_KEY $(date +\"%s\")"
}

function get_time_lock_claimed() {
    echo $($SUDO docker exec ori_redis_1 sh -c "redis-cli -n 1 get $LOCK_TIME_KEY")
}

TO_INDEX_FILE="$HOMEDIR/$TO_INDEX_FILENAME"

LOCKED=$(check_locked)
if [ "$LOCKED" = "$IS_LOCKED" ]; then
    # Send warning if indexing doesn't seem to finish within time limit set
    DATE_STARTED=$(get_time_lock_claimed)
    DATE_NOW=$(date +"%s")
    DATE_DIFF=$(($DATE_NOW-$DATE_STARTED))
    if [ $DATE_DIFF -gt $INDEXING_TIME_LIMIT ]; then
        echo "TOO long ago, SEND MAIL"
    else
        echo "Not too long ago"
    fi
    exit
fi

MUNI=`sed -i -e '1 w /dev/stdout' -e '1d' $TO_INDEX_FILE`
if [ "$MUNI" != "" ];
then
    set_lock "$MUNI"
    $SUDO docker exec ori_backend_1 ./manage.py extract process all \
        --source_path "*"$MUNI \
        --start_date $START_DATE \
        --end_date $END_DATE \
        --lock_key $LOCK_KEY \
        --indexed_filename "$INDEXED_FILENAME"
fi