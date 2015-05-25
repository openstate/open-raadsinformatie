from datetime import datetime

from ocd_backend.items import BaseItem

class TT888Item(BaseItem):
    # Override the default generating of a hash object ID based on the
    # original object id and object urls, and simply use the PRID
    def get_object_id(self):
        return self.original_item['prid']

    # Override the default combined object ID, which is the same as the
    # hash object ID. Instead use the object ID based on the PRID and
    # prepend it with the index name.
    def get_combined_object_id(self):
        return '%s_%s' % (
            self.source_definition['index_name'],
            self.get_object_id()
        )

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

        if self.original_item['prid']:
            combined_index_data['prid'] = self.original_item['prid']

        return combined_index_data

    def get_index_data(self):
        return self.original_item

    def get_all_text(self):
        text_items = []

        if self.original_item['subtitle']:
            # Use only the lines containing the actual subtitles and
            # skip the lines with the time information
            text_items = self.original_item['subtitle'].split('\n')[4::4]

        return u' '.join(text_items)
