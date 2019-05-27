import json
from datetime import datetime

import requests

from ocd_backend.log import get_source_logger
from ocd_backend.loaders import BaseLoader

log = get_source_logger('popit_loader')


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type not serializable")


class PopitLoader(BaseLoader):
    """
    Loads data to a Popit instance.
    """

    def _create_or_update_item(self, item, item_id):
        """
        First tries to post (aka create) a new item. If that does not work,
        do an update (aka put).
        """

        headers = {
            "Apikey": self.source_definition['popit_api_key'],
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        popit_url = "%s/%s" % (
            self.source_definition['popit_base_url'],
            self.source_definition['doc_type'],)
        resp = requests.post(
            popit_url,
            headers=headers, data=json.dumps(item, default=json_serial))

        # popit update controls where we should update the data from ibabs (overwriting our own data)
        # or whether we should only add things when there's new information.
        if (not self.source_definition.get('popit_update', False)) or (resp.status_code != 500):
            return resp

        return requests.put(
            "%s/%s" % (popit_url, item_id,),
            headers=headers, data=json.dumps(item, default=json_serial))

    def load_item(self, doc):
        resp = self._create_or_update_item(doc, doc.get_short_identifier())
