#!/bin/bash
# This script monitors the number of celery processes in the Top 10 of CPU usage. If 0 it
# means processing has stopped.
# Use
#   run via crontab
source ~/.bash_aliases

CELERY_MONITOR_MAIL_FILENAME="celery_monitor_mail_sent.txt"

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

function get_number_of_celery_processes() {
    echo $(ps -A  --sort=-%mem -o "euser pid %mem vsz %cpu args" --cols 140 | head -n 10 | grep celery_app | wc -l)
}

function warn_celery_stopped() {
    if test -f "$HOMEDIR/$CELERY_MONITOR_MAIL_FILENAME"; then
        return
    fi

    EMAIL_TO="developers@openstate.eu"
    FROM_EMAIL="developers@openstate.eu"
    FROM_NAME="Openraadsinformatie Indexing"
    SUBJECT="No celery child processes running"

    bodyHTML="<p>It seems that processing has halted</p>"

    maildata='{"personalizations": [{"to": [{"email": "'${EMAIL_TO}'"}]}],"from": {"email": "'${FROM_EMAIL}'",
	    "name": "'${FROM_NAME}'"},"subject": "'${SUBJECT}'","content": [{"type": "text/html", "value": "'${bodyHTML}'"}]}'

    curl --request POST \
    --url https://api.sendgrid.com/v3/mail/send \
    --header 'Authorization: Bearer '$SENDGRID_API_KEY \
    --header 'Content-Type: application/json' \
    --data "$maildata"

    touch "$HOMEDIR/$CELERY_MONITOR_MAIL_FILENAME"
}

# -----------------------------------------------------------------------------------
# Stop further processing if maintenance file is detected
# Create maintenance file when desired using `touch maintenance.txt`
# -----------------------------------------------------------------------------------
if test -f "$HOMEDIR/$MAINTENANCE_FILE"; then
    echo_to_log "Maintenance, bailing out"
    exit
fi

# -----------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------
N_CELERY_PROCESSES=$(get_number_of_celery_processes)
echo_to_log $N_CELERY_PROCESSES
if [ $N_CELERY_PROCESSES -eq 0 ]; then
    echo_to_log "No celery child processes running, sending warning"

    warn_celery_stopped $DATE_DIFF
fi