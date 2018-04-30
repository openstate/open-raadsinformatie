from ocd_backend.items import BaseItem
from ocd_backend.models import Organization
from ocd_backend.utils.misc import slugify


class MunicipalityOrganisationItem(BaseItem):
    def get_original_object_id(self):
        return unicode(self.original_item['Key']).strip()

    def get_original_object_urls(self):
        return {"html": self.source_definition['file_url']}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        object_model = Organization('cbs_identifier', self.original_item['Key'].strip())
        object_model.name = unicode(self.original_item['Title'])
        object_model.classification = u'Municipality'
        object_model.description = self.original_item['Description']
        return object_model

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)


class AlmanakOrganisationItem(BaseItem):
    def get_object_id(self):
        return slugify(unicode(self.original_item['name']).strip())

    def get_original_object_id(self):
        return unicode(self.original_item['name']).strip()

    def get_original_object_urls(self):
        return {"html": self.source_definition['file_url']}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        object_model = Organization('name', self.original_item['name'])
        #object_model.name = self.original_item['name']
        object_model.description = self.original_item['name']
        return object_model

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
