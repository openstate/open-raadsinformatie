#!/bin/bash
if [ -z "$1" ]; then
    echo "Supply a directory"
    exit
fi

docker exec ori_backend_1 ./manage.py developers process_pdfs --dir=$1 \