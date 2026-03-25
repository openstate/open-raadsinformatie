#!/bin/bash

CONTAINER="ori_elastic_1"
NEW_SNAPSHOT="backup1_$(date +%Y%m%d%H%M)"
sudo docker exec $CONTAINER curl -XPUT http://localhost:9200/_snapshot/local_fs_backups/$NEW_SNAPSHOT