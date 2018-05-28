from datetime import datetime
import re

from ocd_backend.items.popolo import OrganisationItem
from ocd_backend.utils.misc import slugify


class MunicipalityOrganisationItem(OrganisationItem):
    def get_original_object_id(self):
        return unicode(self.original_item['Key']).strip()

    def get_original_object_urls(self):
        return {"html": self.source_definition['file_url']}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

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
    def get_object_id(self):
        prefix = unicode(self.source_definition.get('prefix', '')) + u'-'
        return slugify(
            u'%s%s' % (prefix, unicode(self.original_item['name']).strip(),))

    def get_original_object_id(self):
        prefix = unicode(self.source_definition.get('prefix', '')) + u'-'
        if prefix == u'-':
            prefix = u''
        return u'%s%s' % (prefix, unicode(self.original_item['name']).strip(),)

    def get_original_object_urls(self):
        return {"html": self.source_definition['file_url']}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['id'] = unicode(self.get_object_id())

        combined_index_data['hidden'] = self.source_definition['hidden']
        combined_index_data['name'] = unicode(self.original_item['name'])
        combined_index_data['identifiers'] = [
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
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


class HTMLOrganisationItem(OrganisationItem):
    def get_object_id(self):
        name = unicode(u''.join(self.original_item.xpath('.//text()'))).strip()
        name = re.sub(r'\s*\(\d+ zetels?\)\s*', '', name)
        return slugify(name)

    def get_original_object_id(self):
        name = unicode(u''.join(self.original_item.xpath('.//text()'))).strip()
        name = re.sub(r'\s*\(\d+ zetels?\)\s*', '', name)
        return unicode(name)

    def get_original_object_urls(self):
        return {"html": self.source_definition['file_url']}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['id'] = self.get_object_id()

        combined_index_data['hidden'] = self.source_definition['hidden']
        combined_index_data['name'] = self.get_original_object_id()
        combined_index_data['identifiers'] = [
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            }
        ]
        combined_index_data['classification'] = unicode(
            self.source_definition['classification'])

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
