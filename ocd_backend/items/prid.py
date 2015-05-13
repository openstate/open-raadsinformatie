from datetime import datetime

from ocd_backend.items import BaseItem

class PRIDItem(BaseItem):
    def get_original_object_id(self):
        return self.original_item['PRID']

    def get_original_object_urls(self):
        return {"html": "http://npo.nl/%s/%s/%s" % (
            self.original_item['PRID'],
            self.original_item['broadcast_date'],
            self.original_item['program_name']
        )}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return u'PRID'

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['hidden'] = self.source_definition['hidden']

        if self.original_item['program_name']:
            combined_index_data['title'] = self.original_item['program_name']

        if 'broadcast_date' in self.original_item and self.original_item['broadcast_date']:
            combined_index_data['date'] = datetime.strptime(
                self.original_item['broadcast_date'],
                '%d-%m-%Y'
            )
            combined_index_data['date_granularity'] = 8

        return combined_index_data

    def get_index_data(self):
        return self.original_item

    def get_all_text(self):
        text_items = []

        if self.original_item['program_name']:
            text_items.append(self.original_item['program_name'])

        return u' '.join(text_items)
