#!/bin/bash
FQPATH=`readlink -f $0`
BINDIR=`dirname $FQPATH`
cd $BINDIR/..
tail -n +2 sources.txt >sources.tmp
MUNI=`head -1 sources.txt`
if [ "$MUNI" != "" ];
then
  sudo docker exec ori_backend_1 ./manage.py extract process daily --source_path "*"$MUNI
fi
cp sources.tmp sources.txt
