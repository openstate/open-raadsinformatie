#!/bin/bash
DB_CONTAINER="ori_postgres_1"
DB_NAME="ori"
DB_USER="postgres"

docker exec $DB_CONTAINER pg_dump $DB_NAME -U $DB_USER | gzip > /data/backups/latest-postgresdump-daily.sql.gz
