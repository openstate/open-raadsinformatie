#!/bin/sh
ORI_BACKEND_CONTAINER='ori_backend_1'
# elasticsearch mapping
sudo docker exec $ORI_BACKEND_CONTAINER ./manage.py elasticsearch put_template
# postgres User
# postgres crypto extension hstore thingie
# alembic migrations
