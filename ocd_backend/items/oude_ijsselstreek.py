from datetime import datetime

from ocd_backend.items.popolo import PersonItem


class CouncilItem(PersonItem):
    def get_original_object_id(self):
        print self.original_item.xpath('.//a//text()')
        return unicode(self.original_item.xpath('.//a//text()')[0])

    def get_original_object_urls(self):
        return {"html": self.source_definition['file_url']}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return u'Oude Ijsselstreek'

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['hidden'] = self.source_definition['hidden']

        combined_index_data['name'] = unicode(self.original_item.xpath(
            './/img/@title')[0])
        combined_index_data['biography'] = u''.join(
            self.original_item.xpath('.//text()'))
        combined_index_data['created_at'] = datetime.strptime(
            u'2015-05-19', '%Y-%m-%d')

        # combined_index_data['media_urls'] = []
        # combined_index_data['media_urls'].append({
        #     'original_url': (
        #         u'http://www.oude-ijsselstreek.nl' + self.original_item.xpath(
        #             './/img/@src')[0]),
        #     'content_type': 'image/jpeg'
        # })
        combined_index_data['image'] = (
            u'http://www.oude-ijsselstreek.nl' + self.original_item.xpath(
                './/img/@src')[0])

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        # if self.original_item['info']:
        #     text_items.append(self.original_item['info'])
        #
        # if self.original_item['aflevering_titel']:
        #     text_items.append(self.original_item['aflevering_titel'])
        #
        # if self.original_item['titel']:
        #     text_items.append(self.original_item['titel'])
        #
        # if self.original_item['prid']:
        #     text_items.append(self.original_item['prid'])
        #
        # if self.original_item['omroepen']:
        #     for broadcaster in self.original_item['omroepen']:
        #         if broadcaster['naam']:
        #             text_items.append(broadcaster['naam'])

        return u' '.join(text_items)
