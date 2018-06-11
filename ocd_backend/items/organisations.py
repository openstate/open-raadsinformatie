from ocd_backend.items import BaseItem
from ocd_backend.models import Organization, AlmanakOrganizationName
from ocd_backend.models.model import Relationship


class MunicipalityOrganisationItem(BaseItem):
    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        object_model = Organization()#'cbs_identifier', self.original_item['Key'])
        object_model.name = unicode(self.original_item['Title'])
        object_model.classification = u'Municipality'
        object_model.description = self.original_item['Description']

        a = Organization()
        a.name = 'a'

        b = Organization()
        b.name = 'b'

        c = Organization()
        c.name = 'c'

        object_model.parent = Relationship(a, b, rel=c)

        return object_model


class AlmanakOrganisationItem(BaseItem):
    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        object_model = Organization(AlmanakOrganizationName, 'name', self.original_item['name'])
        object_model.name = self.original_item['name'] #todo dubbel?
        object_model.classification = self.original_item['classification']
        return object_model
