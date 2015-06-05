from datetime import datetime

from ocd_backend.items.popolo import OrganisationItem


class MunicipalityOrganisationItem(OrganisationItem):
    def get_original_object_id(self):
        return unicode(self.original_item['Key']).strip()

    def get_original_object_urls(self):
        return {"html": self.source_definition['file_url']}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['filter']['Title'])

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['id'] = unicode(self.get_object_id())

        combined_index_data['hidden'] = self.source_definition['hidden']
        combined_index_data['name'] = unicode(self.original_item['Title'])
        combined_index_data['identifiers'] = [
            {
                'identifier': self.original_item['Key'].strip(),
                'scheme': u'CBS'
            },
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            }
        ]
        combined_index_data['classification'] = u'Municipality'
        combined_index_data['description'] = self.original_item['Description']

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)


class AlmanakOrganisationItem(OrganisationItem):
    def get_original_object_id(self):
        return unicode(self.original_item['name']).strip()

    def get_original_object_urls(self):
        return {"html": self.source_definition['file_url']}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.original_item['name'])

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['id'] = unicode(self.get_object_id())

        combined_index_data['hidden'] = self.source_definition['hidden']
        combined_index_data['name'] = unicode(self.original_item['name'])
        combined_index_data['identifiers'] = [
            {
                'identifier': self.get_object_id(),
                'scheme': u'Almanak'
            }
        ]
        combined_index_data['classification'] = self.original_item[
            'classification']
        combined_index_data['description'] = self.original_item['name']

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
