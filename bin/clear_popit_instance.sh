#!/bin/sh

for popit_entity in memberships persons organizations; do echo $popit_entity; for popit_id in `wget -qO - "http://utrecht2.openraadsinformatie.nl/api/v0.1/$popit_entity/" |jq '.result |.[] |.id' |sed -e 's/\"//g;'`; do curl -XDELETE -H 'Apikey: d9f780bce2f2e6d6a2101208a40feacabd883522' "http://utrecht2.openraadsinformatie.nl/api/v0.1/$popit_entity/$popit_id"; echo "* $popit_id"; done; done
