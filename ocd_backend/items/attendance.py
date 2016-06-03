from datetime import datetime
import iso8601

from ocd_backend.items import BaseItem
from ocd_backend.items.popolo import EventItem


class AttendanceForEventItem(BaseItem):
    combined_index_fields = {
        'id': unicode,
        'hidden': bool,
        'doc': dict
    }

    def get_object_id(self):
        return unicode(self.original_item['id'])

    def get_original_object_id(self):
        return self.get_object_id()

    def get_original_object_urls(self):
        try:
            return self.original_item['meta']['original_object_urls']
        except KeyError as e:
            return {'html': self.original_item['html_url']}

    def get_rights(self):
        try:
            return self.original_item['meta']['rights']
        except KeyError as e:
            return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['id'] = self.original_item['id']

        combined_index_data['hidden'] = self.source_definition['hidden']
        combined_index_data['doc'] = {
            'attendees': []
        }

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
