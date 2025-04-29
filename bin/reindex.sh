#!/bin/bash
# This script will reindex all sources listed in $TO_INDEX_FILENAME, and can be run for
# each supplier separately. The sources in $TO_INDEX_FILENAME can be prepared using
#   sudo docker exec ori_backend_1 ./manage.py extract list_sources --sources_config ./ocd_backend/sources/ori.notubiz.yaml |tail -n +2 |grep ' -s '|sed 's/ - //' |sed 's/ -s /./' >sources_notubiz.txt
#
# Use
#   bin/reindex
# without any parameters to process all sources sequentially.
# Pass a supplier e.g.
#   bin/reindex notubiz
# and start multiple processes for parallel processing.
#
# Run this script periodically using crontab to check if the next source can be started.
#
# It will only start the next source if the lock has been released for the previous.
#
# If too much time elapses before the lock is released, a mail is sent (once) to warn about potential problems.
#
# Start and end times of processing are written to $INDEXED_FILENAME.
# If you want this script not to pick up the next source after the current one finishes, do a
#       touch maintenance.txt
#
# PRACTICAL CONSIDERATIONS:
# - Whenever an uncaught error is raised the lock will not be released. This allows for fixing errors
#   in an early stage and getting as close to 100% coverage as possible
# - When an error has been fixed for a source:
#   - if there are still other sources running:
#       - touch maintenance.txt
#       - pkill -9 celery
#       - sudo docker exec ori_redis_1 redis-cli --scan --pattern '*' |sudo xargs docker exec ori_redis_1 redis-cli del
#       - to check: sudo docker exec -it ori_redis_1 redis-cli keys \*
#       - add the source that was still running on top of to_index_ABC.txt again
#       - delete the redis lock: `sudo docker exec ori_redis_1 sh -c "redis-cli -n 1 del ori_lock_key_ABC"`
#   - add the source to the top of to_index_XYZ.txt again (sudo docker exec ori_redis_1 sh -c "redis-cli -n 1 get ori_lock_key_XYZ")
#   - delete the redis lock: `sudo docker exec ori_redis_1 sh -c "redis-cli -n 1 del ori_lock_key_XYZ"`
#   - git pull
#   - sudo docker compose --compatibility up --build -d
#   - rm maintenance.txt
# - The source (and other sources) will again be processed
SUDO="sudo " # In development substitute with empty string
source ~/.bash_aliases
MAINTENANCE_FILE="maintenance.txt"
IS_LOCKED="ori_is_locked"

SUPPLIERS=(notubiz ibabs go parlaeus)
SUPPLIER_SUFFIX=""
for ((i=0; i < ${#SUPPLIERS[@]}; i++)); do
    if [ "${SUPPLIERS[i]}" == "$1" ]; then
        SUPPLIER_SUFFIX="_$1"
    fi
done

TO_INDEX_FILENAME="to_index${SUPPLIER_SUFFIX}.txt"
LOCK_KEY="ori_lock_key${SUPPLIER_SUFFIX}"
LOCK_TIME_KEY="ori_lock_time_key${SUPPLIER_SUFFIX}"
MAIL_SENT_KEY="ori_mail_sent${SUPPLIER_SUFFIX}"
MAINTENANCE_MAIL_FILENAME="maintenance${SUPPLIER_SUFFIX}_sent.txt"

INDEXED_FILENAME="indexed${SUPPLIER_SUFFIX}.log"
START_DATE='2010-01-01'
END_DATE=`date -d "-1 day" +%Y-%m-%d`
INDEXING_TIME_LIMIT=86400 # a day in seconds

FQPATH=`readlink -f $0`
BINDIR=`dirname $FQPATH`
HOMEDIR=`dirname $BINDIR`
cd $HOMEDIR

# -----------------------------------------------------------------------------------
# Function definitions
# -----------------------------------------------------------------------------------
function echo_to_log() {
    local message=$1
    echo "$(date): $message"
}
echo -e "\n"

function get_locked_source() {
    echo $($SUDO docker exec ori_redis_1 sh -c "redis-cli -n 1 get $LOCK_KEY")
}
echo_to_log $(get_locked_source)

function check_locked() {
    local locked_source=$(get_locked_source)
    if [ -n "$locked_source" ]; then
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

function set_mail_sent() {
    local source=$1
    $SUDO docker exec ori_redis_1 sh -c "redis-cli -n 1 set $MAIL_SENT_KEY $source"
}

function mail_sent() {
    local source=$1
    local mail_sent=$($SUDO docker exec ori_redis_1 sh -c "redis-cli -n 1 get $MAIL_SENT_KEY")
    if [ "$source" = "$mail_sent" ]; then
        echo "yes"
    else
        echo "no"
    fi
}

function clear_mail_sent() {
    $SUDO docker exec ori_redis_1 sh -c "redis-cli -n 1 del $MAIL_SENT_KEY"
}

function warn_processing_time() {
    local date_diff=$1
    local locked_source=$(get_locked_source)

    mail_was_sent=$(mail_sent $locked_source)
    if [ "$mail_was_sent" = "yes" ]; then
        echo_to_log "Mail has already been sent"
        return
    fi

    EMAIL_TO="developers@openstate.eu"
    FROM_EMAIL="developers@openstate.eu"
    FROM_NAME="Openraadsinformatie Indexing"
    SUBJECT="Processing $locked_source ($SUPPLIER_SUFFIX) is taking too long"

    bodyHTML="<p>Processing started $date_diff seconds ago</p>"

    maildata='{"personalizations": [{"to": [{"email": "'${EMAIL_TO}'"}]}],"from": {"email": "'${FROM_EMAIL}'",
	    "name": "'${FROM_NAME}'"},"subject": "'${SUBJECT}'","content": [{"type": "text/html", "value": "'${bodyHTML}'"}]}'

    curl --request POST \
    --url https://api.sendgrid.com/v3/mail/send \
    --header 'Authorization: Bearer '$SENDGRID_API_KEY \
    --header 'Content-Type: application/json' \
    --data "$maildata"

    set_mail_sent $locked_source
}

function warn_suspended_due_to_maintenance() {
    if test -f "$HOMEDIR/$MAINTENANCE_MAIL_FILENAME"; then
        return
    fi

    EMAIL_TO="developers@openstate.eu"
    FROM_EMAIL="developers@openstate.eu"
    FROM_NAME="Openraadsinformatie Indexing"
    SUBJECT="Previous processing for $SUPPLIER_SUFFIX has finished but maintenance file encountered"

    bodyHTML="<p>If all processing has finished you can update the sources.</p>"

    maildata='{"personalizations": [{"to": [{"email": "'${EMAIL_TO}'"}]}],"from": {"email": "'${FROM_EMAIL}'",
	    "name": "'${FROM_NAME}'"},"subject": "'${SUBJECT}'","content": [{"type": "text/html", "value": "'${bodyHTML}'"}]}'

    curl --request POST \
    --url https://api.sendgrid.com/v3/mail/send \
    --header 'Authorization: Bearer '$SENDGRID_API_KEY \
    --header 'Content-Type: application/json' \
    --data "$maildata"

    touch "$HOMEDIR/$MAINTENANCE_MAIL_FILENAME"
}

# -----------------------------------------------------------------------------------
# Check if previous source is still being processed. If so, bail out. Send warning
# if processing takes too long.
# -----------------------------------------------------------------------------------
LOCKED=$(check_locked)
if [ "$LOCKED" = "$IS_LOCKED" ]; then
    echo_to_log "Indexing busy, not starting new source"

    # Send warning if indexing doesn't seem to finish within time limit set
    DATE_STARTED=$(get_time_lock_claimed)
    DATE_NOW=$(date +"%s")
    DATE_DIFF=$(($DATE_NOW-$DATE_STARTED))
    echo_to_log "date started $DATE_STARTED $DATE_NOW $DATE_DIFF"
    if [ $DATE_DIFF -gt $INDEXING_TIME_LIMIT ]; then
        echo_to_log "TOO long ago, SEND MAIL"
        warn_processing_time $DATE_DIFF
    fi
    exit
fi

# -----------------------------------------------------------------------------------
# Stop further processing if maintenance file is detected
# Create maintenance file when desired using `touch maintenance.txt`
# -----------------------------------------------------------------------------------
if test -f "$HOMEDIR/$MAINTENANCE_FILE"; then
    echo_to_log "Maintenance, bailing out"
    warn_suspended_due_to_maintenance
    exit
fi

# -----------------------------------------------------------------------------------
# Get next entry from TO_INDEX_FILE and start processing
# -----------------------------------------------------------------------------------
TO_INDEX_FILE="$HOMEDIR/$TO_INDEX_FILENAME"
SOURCE=`sed -i -e '1 w /dev/stdout' -e '1d' $TO_INDEX_FILE`
if [ "$SOURCE" != "" ];
then
    clear_mail_sent
    set_lock "$SOURCE"
    $SUDO docker exec ori_backend_1 sh -c "./manage.py extract process all \
        --source_path $SOURCE \
        --start_date $START_DATE \
        --end_date $END_DATE \
        --lock_key $LOCK_KEY \
        --indexed_filename \"$INDEXED_FILENAME\" >> /opt/ori/data/ori.log 2>&1"
fi
