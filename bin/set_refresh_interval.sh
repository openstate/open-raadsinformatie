#!/bin/bash
# Usage:
#   Run this on the server (api.openraadsinformatie.nl does not allow PUT requests for security reasons)
#       bin/set_refresh_interval.sh
IP_ADDRESS=`sudo docker inspect ori_elastic_1 | grep IPAddress | tail -1 | awk -F "\"" '{print $4}'`
curl -H 'Content-type: application/json' 'http://'$IP_ADDRESS':9200/_settings' -XPUT -d '{
  "index": {
    "refresh_interval" : "30s"
  }
}'
