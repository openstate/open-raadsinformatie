#!/bin/sh

# source /opt/bin/activate
cd /opt/ori

touch counts.txt
touch counts-old.txt
cp counts.txt counts-old.txt
wget -q -O - http://elastic:9200/_cat/indices |awk '{print $3, $7}' > counts.txt
cat counts.txt counts-old.txt |sort |uniq -c |awk '$1 > 1 {print}'
