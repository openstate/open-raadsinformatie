#!/bin/sh
ORI_BACKEND_CONTAINER='ori_backend_1'
ORI_POSTGRES_CONTAINER='ori_postgres_1'
# elasticsearch mapping
sudo docker exec $ORI_BACKEND_CONTAINER ./manage.py elasticsearch put_template
# postgres User
PG_USER="${POSTGRES_USERNAME:-ori_postgres_user}"
PG_PASSWD="${POSTGRES_PASSWORD:-ori_postgres_password}"
sudo docker exec -it $ORI_POSTGRES_CONTAINER psql -U postgres -c "CREATE USER $PG_USER PASSWORD '$PG_PASSWD';"
# create database
PG_DB="${POSTGRES_DATABASEE:-ori}"
sudo docker exec -it $ORI_POSTGRES_CONTAINER psql -U postgres -c "CREATE DATABASE $PG_DB;"
# postgres crypto extension hstore thingie
sudo docker exec -it $ORI_POSTGRES_CONTAINER psql -U postgres $PG_DB -c "CREATE EXTENSION pgcrypto;"
# alembic migrations
sudo docker exec -it -w /opt/ori/ocd_backend/alembic $ORI_BACKEND_CONTAINER alembic upgrade head
