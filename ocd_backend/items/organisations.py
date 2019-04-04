import re

from ocd_backend.items import BaseItem
from ocd_backend.models import Organization


class MunicipalityOrganisationItem(BaseItem):
    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        source_defaults = {
            'source': 'cbs',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        object_model = Organization(self.original_item['Key'], **source_defaults)
        object_model.name = unicode(self.original_item['Title'])
        object_model.classification = u'Municipality'
        object_model.description = self.original_item['Description']
        object_model.collection = self.get_collection()
        return object_model


class AlmanakOrganisationItem(BaseItem):
    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        source_defaults = {
            'source': 'almanak',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        object_model = Organization(
            self.original_item['name'], **source_defaults)
        object_model.name = self.original_item['name']  # todo dubbel?
        object_model.classification = self.original_item['classification']
        object_model.parent = Organization(self.source_definition['almanak_id'], **source_defaults)
        object_model.parent.merge(collection=self.source_definition['index_name'])

        return object_model


class HTMLOrganisationItem(BaseItem):

    def _get_name(self):
        name = unicode(u''.join(self.original_item.xpath('.//text()'))).strip()
        name = re.sub(r'\s*\(\d+ zetels?\)\s*', '', name)
        return unicode(name)

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        source_defaults = {
            'source': 'almanak',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        object_model = Organization(
            self._get_name(), **source_defaults)
        object_model.name = self._get_name()  # todo dubbel?
        object_model.classification = unicode(
            self.source_definition.get('classification', 'Party'))
        object_model.collection = self.get_collection()

        return object_model
