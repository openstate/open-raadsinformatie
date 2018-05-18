#!/bin/sh

#nosetests -l debug --nocapture --with-coverage --cover-package=ocd_backend,ocd_frontend --cover-inclusive
nosetests --with-coverage --cover-package=ocd_backend,ocd_frontend --cover-inclusive
