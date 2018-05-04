#!/bin/sh
cd /opt/ori
python -c 'import requests; print requests.delete("http://elasticsearch:9200/ori_*/")'
./manage.py elasticsearch put_template
./manage.py elasticsearch create_indexes es_mappings/
