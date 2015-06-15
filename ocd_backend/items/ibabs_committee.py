from datetime import datetime
import json
from pprint import pprint

import iso8601

from ocd_backend.items.popolo import OrganisationItem
from ocd_backend.utils.misc import slugify
from ocd_backend import settings
from ocd_backend.extractors import HttpRequestMixin


class CommitteeItem(OrganisationItem):
    def get_object_id(self):
        return slugify(unicode(self.original_item['Meetingtype']).strip())

    def get_original_object_id(self):
        return unicode(self.original_item['Meetingtype']).strip()

    def get_original_object_urls(self):
        # TODO: we should fix this, but I have no idea how :P
        return {"html": self.original_item['Meetingtype']}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.original_item['Meetingtype'])

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['id'] = unicode(self.get_object_id())

        combined_index_data['hidden'] = self.source_definition['hidden']
        combined_index_data['name'] = unicode(
            self.original_item['Meetingtype'])
        combined_index_data['identifiers'] = [
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            },
            {
                'identifier': self.original_item['Id'],
                'scheme': u'iBabs'
            }
        ]
        if 'sub' in self.original_item['Meetingtype']:
            classification = u'subcommittee'
        else:
            classification = u'committee'
        combined_index_data['classification'] = classification
        combined_index_data['description'] = combined_index_data['name']

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
