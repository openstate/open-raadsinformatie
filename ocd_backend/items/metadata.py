from datetime import datetime

from ocd_backend.items import BaseItem

class MetadataItem(BaseItem):
    def get_original_object_id(self):
        return self.original_item['prid']

    def get_original_object_urls(self):
        return {"html": "http://e.omroep.nl/metadata/%s" % (
            self.original_item['prid']
        )}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return u'metadata'

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['hidden'] = self.source_definition['hidden']

        if self.original_item['titel']:
            combined_index_data['title'] = self.original_item['titel']

        if 'aflevering_titel' in self.original_item and self.original_item['aflevering_titel']:
            combined_index_data['description'] = self.original_item['aflevering_titel']

        if 'gidsdatum' in self.original_item and self.original_item['gidsdatum']:
            combined_index_data['date'] = datetime.strptime(
                self.original_item['gidsdatum'],
                '%Y-%m-%d'
            )
            combined_index_data['date_granularity'] = 8

        if self.original_item['omroepen']:
            authors = []
            for broadcaster in self.original_item['omroepen']:
                if broadcaster['naam'] and broadcaster['naam'] not in authors:
                    authors.append(broadcaster['naam'])

            if authors:
                combined_index_data['authors'] = authors

        if 'images' in self.original_item and self.original_item['images']:
            combined_index_data['media_urls'] = []
            for image in self.original_item['images']:
                (width, height) = image['size'].split('x')
                combined_index_data['media_urls'].append({
                    'original_url': image['url'],
                    'content_type': 'image/jpeg',
                    'width': width,
                    'height': height
                })

        return combined_index_data

    def get_index_data(self):
        return self.original_item

    def get_all_text(self):
        text_items = []

        if self.original_item['info']:
            text_items.append(self.original_item['info'])

        if self.original_item['aflevering_titel']:
            text_items.append(self.original_item['aflevering_titel'])

        if self.original_item['titel']:
            text_items.append(self.original_item['titel'])

        if self.original_item['prid']:
            text_items.append(self.original_item['prid'])

        if self.original_item['omroepen']:
            for broadcaster in self.original_item['omroepen']:
                if broadcaster['naam']:
                    text_items.append(broadcaster['naam'])

        return u' '.join(text_items)
