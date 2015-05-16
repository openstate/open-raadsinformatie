from datetime import datetime

from ocd_backend.items import BaseItem

class TT888Item(BaseItem):
    # Overrule the default generating of a hash object id based on the
    # original object id and object urls, and simply use the object
    # id/prid.
    def get_object_id(self):
        return self.original_item['prid']

    def get_original_object_id(self):
        return self.original_item['prid']

    def get_original_object_urls(self):
        return {"html": "http://e.omroep.nl/tt888/%s" % (
            self.original_item['prid']
        )}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return u'tt888'

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['hidden'] = self.source_definition['hidden']

        return combined_index_data

    def get_index_data(self):
        return self.original_item

    def get_all_text(self):
        text_items = []

        if self.original_item['subtitle']:
            # Use only the lines containing the actual subtitles and
            # skip the lines with the time information
            text_items = self.original_item['subtitle'].split('\n')[4::4]

        print text_items
        return u' '.join(text_items)
