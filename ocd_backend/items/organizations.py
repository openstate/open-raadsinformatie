from ocd_backend.items import BaseItem
from ocd_backend.models import TopLevelOrganization, Organization


def transform_contact_details(data):
    """
    Takes a dictionary of contact details and flattens every entry to {key: {label: label, value: value} .
    """

    transformed_data = {}
    for key, value in data.items():
        if 'label' in value:
            transformed_data[key] = value
        else:
            for key2, value2 in value.items():
                transformed_data['%s_%s' % (key, key2)] = {'label': key2, 'value': value2}

    return transformed_data


class MunicipalityOrganizationItem(BaseItem):
    """
    Creates a Municipality item.
    """

    def get_rights(self):
        return u'undefined'

    def get_object_model(self):
        source_defaults = {
            'source': 'allmanak',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        object_model = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        object_model.classification = u'Municipality'
        object_model.collection = self.source_definition['key']
        object_model.name = ' '.join([self.source_definition.get('municipality_prefix', ''), unicode(self.original_item['naam'])])
        object_model.description = self.original_item['omvatplaats']
        # object_model.contact_details = transform_contact_details(self.original_item['contact'])

        return object_model


class ProvinceOrganizationItem(BaseItem):
    """
    Creates a Province item.
    """

    def get_rights(self):
        return u'undefined'

    def get_object_model(self):
        source_defaults = {
            'source': 'allmanak',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        object_model = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        object_model.classification = u'Province'
        object_model.collection = self.source_definition['key']
        object_model.name = unicode(self.original_item['naam'])
        object_model.description = self.original_item['omvatplaats']
        # object_model.contact_details = transform_contact_details(self.original_item['contact'])

        return object_model


class AlmanakOrganisationItem(BaseItem):
    """
    Extracts organizations from the Almanak. The source file calling this item must set a `classification`
    for the entity because there are several types of organisations (councils, parties, etc.)
    """

    def get_rights(self):
        return u'undefined'

    def get_object_model(self):

        if not self.source_definition['classification']:
            raise ValueError('You must set a classification in the source file to use AlmanakOrganisationItem.')

        source_defaults = {
            'source': 'almanak',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        if self.source_definition['classification'] == "Province":
            object_model = TopLevelOrganization(self.original_item, **source_defaults)
            object_model.name = self.original_item
            object_model.classification = self.source_definition['classification']
            object_model.collection = self.source_definition['key']
        else:
            object_model = Organization(self.original_item, **source_defaults)
            object_model.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
            object_model.has_organization_name.merge(collection=self.source_definition['key'])
            object_model.name = self.original_item
            object_model.classification = self.source_definition['classification']
            object_model.subOrganizationOf = TopLevelOrganization(self.source_definition['key'], **source_defaults)
            object_model.subOrganizationOf.merge(collection=self.source_definition['key'])

        return object_model


class HTMLOrganisationItem(BaseItem):

    def _get_name(self, item):
        name = unicode(u''.join(item.xpath('.//text()'))).strip()
        # name = re.sub(r'\s*\(\d+ zetels?\)\s*', '', name)
        return unicode(name)

    def get_rights(self):
        return u'undefined'

    def get_object_model(self):

        if not self.source_definition['classification']:
            raise ValueError('You must set a classification in the source file to use HTMLOrganisationItem.')

        source_defaults = {
            'source': 'almanak',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        if self.source_definition['classification'] == "Province":
            object_model = TopLevelOrganization(self._get_name(self.original_item), **source_defaults)
            object_model.name = self._get_name(self.original_item)
            object_model.collection = self.source_definition['key']
            object_model.classification = self.source_definition['classification']
        else:
            object_model = Organization(self._get_name(self.original_item), **source_defaults)
            object_model.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
            object_model.has_organization_name.merge(collection=self.source_definition['key'])
            object_model.name = self._get_name(self.original_item)
            object_model.classification = self.source_definition['classification']
            object_model.subOrganizationOf = TopLevelOrganization(self.source_definition['key'], **source_defaults)
            object_model.subOrganizationOf.merge(collection=self.source_definition['key'])

        return object_model
