#!/usr/bin/env python

# ./convert.py 'http://openri.127.0.0.1.xip.io:5000/api/v0.1' \
# 46143143cd126fb7d1fe3cba4a2657c15c2d8250 amstelveen_organisations.json \
# amstelveen_persons.json

import sys
import os
import re
import json
import codecs
from pprint import pprint
import hashlib

import requests

def md5str(text):
    m = hashlib.md5()
    m.update(text)
    return m.hexdigest()

def main(argv=None):
    if argv is None:
        argv=sys.argv

    base_url = argv[1]
    api_key = argv[2]

    headers = {
        "Apikey": api_key,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    contents = "{\"organizations\": []}"
    with codecs.open(argv[3], 'r', 'utf-8') as infile:
        contents = infile.read()
    organisations = json.loads(
        contents.replace('organisation', 'organization'))['organizations']

    contents = "{\"persons\": []}"
    with codecs.open(argv[4], 'r', 'utf-8') as infile:
        contents = infile.read()
    persons = json.loads(
        contents.replace('organisation', 'organization'))['persons']

    for org in organisations:
        org['memberships'] = []
        resp = requests.post("%s/organizations" % (base_url,), headers=headers, json=org)
        if resp.status_code == 500:
            resp = requests.put("%s/organizations/%s" % (base_url, org['id'],), headers=headers, json=org)

    # some persons appear twice ;)
    persons_done = {}
    for person in persons:
        if not persons_done.has_key(person['name']):
            persons_done[person['name']] = person
        else:
            persons_done[person['name']]['memberships'] += person['memberships']
            for m in persons_done[person['name']]['memberships']:
                m['person_id'] = persons_done[person['name']]['id']

    for person in persons_done.values():
        # pprint(person)
        resp = requests.post("%s/persons" % (base_url,), headers=headers, json=person)
        if resp.status_code == 500:
            resp = requests.put("%s/persons/%s" % (base_url, org['id'],), headers=headers, json=org)
        for membership in person['memberships']:
            membership['id'] = md5str(u'%s-%s' % (
                membership['person_id'], membership['organization_id'],))
            # membership['start_date'] = u'2014-01'
            resp = requests.post("%s/memberships" % (base_url,), headers=headers, json=membership)
            print resp.status_code

    return 0

if __name__ == '__main__':
   sys.exit(main())
