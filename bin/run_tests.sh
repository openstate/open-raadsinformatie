#!/bin/sh

#nosetests -l debug --nocapture --with-coverage --cover-package=ocd_backend --cover-inclusive
nosetests --with-coverage --cover-package=ocd_backend --cover-inclusive
