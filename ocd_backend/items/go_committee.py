from ocd_backend.items.popolo import OrganisationItem

from ocd_backend.utils.misc import slugify


class CommitteeItem(OrganisationItem):
    def get_object_id(self):
        return slugify(unicode(self.original_item['name']).strip())

    def get_original_object_id(self):
        return unicode(self.original_item['name']).strip()

    def get_original_object_urls(self):
        return {"html": self.original_item['archive']}

    @staticmethod
    def get_rights():
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        object_model = dict()

        object_model['id'] = unicode(self.get_object_id())

        object_model['hidden'] = self.source_definition['hidden']
        object_model['name'] = unicode(
            self.original_item['name'])
        object_model['identifiers'] = [
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            },
            {
                'identifier': unicode(self.original_item['name']),
                'scheme': u'GemeenteOplossingen'
            }
        ]
        if 'sub' in self.original_item['name']:
            classification = u'subcommittee'
        else:
            classification = u'committee'
        object_model['classification'] = classification
        object_model['description'] = object_model['name']

        return object_model

    @staticmethod
    def get_index_data():
        return {}

    @staticmethod
    def get_all_text():
        text_items = []

        return u' '.join(text_items)
