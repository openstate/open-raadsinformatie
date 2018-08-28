from ocd_backend.items import BaseItem
from ocd_backend.models import Motion, Organization


class PartijgedragMotion(BaseItem):
    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        source_defaults = {
            'source': 'partijgedrag',
            'source_id_key': 'identifier',
            'organization': 'ggm',
        }

        object_model = Motion(self.original_item['id'], **source_defaults)
        object_model.name = self.original_item['name']
        object_model.text = self.original_item['text']
        object_model.date = self.original_item['date']
        object_model.legislative_session = self.original_item['legislative_session']
        if self.original_item['creator']:
            object_model.creator = [
                Organization(x, **source_defaults) for x in self.original_item['creator'].split(',')
            ]
        object_model.organization = Organization('TK', **source_defaults)

        return object_model
