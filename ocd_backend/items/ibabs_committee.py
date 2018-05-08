from ocd_backend.items.popolo import OrganisationItem
from ocd_backend.utils.misc import slugify


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
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        object_model = {}

        object_model['id'] = unicode(self.get_object_id())

        object_model['hidden'] = self.source_definition['hidden']
        object_model['name'] = unicode(
            self.original_item['Meetingtype'])
        object_model['identifiers'] = [
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
        object_model['classification'] = classification
        object_model['description'] = object_model['name']

        return object_model

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
