import re

from ocd_backend.items import BaseItem
from ocd_backend.models import Organization


class MunicipalityOrganisationItem(BaseItem):
    """
    Extracts municipality information from the Almanak.
    """

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
    """
    Extracts organizations from the Almanak. The source file calling this item must set a `classification`
    for the entity because there are serveral types of organisations (councils, parties, etc.)
    """

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):

        if not self.source_definition['classification']:
            raise ValueError('You must set a classification in the source file to use AlmanakOrganisationItem.')

        source_defaults = {
            'source': 'almanak',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        object_model = Organization(self.original_item, **source_defaults)
        object_model.name = self.original_item  # todo dubbel?
        object_model.classification = self.source_definition['classification']

        if self.source_definition['classification'] == "Province":
            object_model.collection = self.source_definition['key']

        if self.source_definition['classification'] != "Province":
            object_model.subOrganizationOf = Organization(self.source_definition['key'], **source_defaults)
            object_model.subOrganizationOf.merge(collection=self.source_definition['key'])

        return object_model


class HTMLOrganisationItem(BaseItem):

    def _get_name(self, item):
        name = unicode(u''.join(item.xpath('.//text()'))).strip()
        # name = re.sub(r'\s*\(\d+ zetels?\)\s*', '', name)
        return unicode(name)

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):

        if not self.source_definition['classification']:
            raise ValueError('You must set a classification in the source file to use HTMLOrganisationItem.')

        source_defaults = {
            'source': 'almanak',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        object_model = Organization(self._get_name(self.original_item), **source_defaults)
        object_model.name = self._get_name(self.original_item)
        object_model.classification = self.source_definition['classification']

        if self.source_definition['classification'] != "Province":
            object_model.subOrganizationOf = Organization(self.source_definition['key'], **source_defaults)
            object_model.subOrganizationOf.merge(collection=self.source_definition['key'])

        return object_model
