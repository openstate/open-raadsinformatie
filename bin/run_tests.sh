#!/bin/sh
if [ -z "$1" ]; then
  NOSE2_OPTIONS='-s tests'
else  
  NOSE2_OPTIONS="$1"
fi

cd /opt/ori
nose2 -v $NOSE2_OPTIONS
