from ocd_backend import celery_app
from ocd_backend.transformers import BaseTransformer
from ocd_backend.models import *
from ocd_backend.log import get_source_logger

log = get_source_logger('organizations')


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


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=(Exception,), retry_backoff=True)
def municipality_organization_item(self, content_type, raw_item, entity, source_item, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'allmanak',
        'collection': 'municipality',
    }

    object_model = TopLevelOrganization(original_item['systemid'],
                                        self.source_definition,
                                        **source_defaults)
    object_model.entity = entity
    object_model.classification = u'Municipality'
    object_model.collection = self.source_definition['key']
    object_model.name = ' '.join([self.source_definition.get('municipality_prefix', ''), unicode(original_item['naam'])])
    object_model.description = original_item['omvatplaats']
    # object_model.contact_details = transform_contact_details(original_item['contact'])

    object_model.save()
    return object_model


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=(Exception,), retry_backoff=True)
def province_organization_item(self, content_type, raw_item, entity, source_item, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'allmanak',
        'collection': 'province',
    }

    object_model = TopLevelOrganization(original_item['systemid'],
                                        self.source_definition,
                                        **source_defaults)
    object_model.entity = entity
    object_model.classification = u'Province'
    object_model.collection = self.source_definition['key']
    object_model.name = unicode(original_item['naam'])
    object_model.description = original_item['omvatplaats']
    # object_model.contact_details = transform_contact_details(original_item['contact'])

    object_model.save()
    return object_model


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=(Exception,), retry_backoff=True)
def party_item(self, content_type, raw_item, entity, source_item, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'allmanak',
        'collection': 'party',
    }

    # When the Allmanak implements parties as entities, the entity ID should be used
    object_model = Organization(original_item['partij'],
                                self.source_definition,
                                **source_defaults)
    object_model.entity = entity
    object_model.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                              source=self.source_definition['key'],
                                                              supplier='allmanak',
                                                              collection=self.source_definition['source_type'])
    object_model.collection = self.source_definition['key'] + '-' + original_item['partij']
    object_model.name = original_item['partij']
    object_model.classification = 'Party'
    object_model.subOrganizationOf = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                          source=self.source_definition['key'],
                                                          supplier='allmanak',
                                                          collection=self.source_definition['source_type'])

    object_model.save()
    return object_model
