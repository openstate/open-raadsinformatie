from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.models import *
from ocd_backend.transformers import BaseTransformer
from ocd_backend.settings import AUTORETRY_EXCEPTIONS, RETRY_MAX_RETRIES, AUTORETRY_RETRY_BACKOFF, AUTORETRY_RETRY_BACKOFF_MAX

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


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=AUTORETRY_EXCEPTIONS,
                 retry_backoff=AUTORETRY_RETRY_BACKOFF, max_retries=RETRY_MAX_RETRIES, retry_backoff_max=AUTORETRY_RETRY_BACKOFF_MAX)
def municipality_organization_item(self, content_type, raw_item, canonical_iri, cached_path, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    try:
        classification = self.source_definition['classification']
    except LookupError as e:
        classification = 'Municipality'
    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'allmanak',
        'collection': 'municipality',
        'canonical_iri': canonical_iri,
        'cached_path': cached_path,
    }

    object_model = TopLevelOrganization(original_item['systemid'], **source_defaults)
    object_model.classification = classification
    object_model.collection = self.source_definition['key']
    object_model.name = ' '.join([self.source_definition.get('municipality_prefix', ''), original_item['naam']])
    object_model.description = original_item['omvatplaats']
    try:
        object_model.homepage = original_item['contact']['internet']['value']
        object_model.email = original_item['contact']['emailadres']['value']
    except KeyError:
        pass
    # object_model.contact_details = transform_contact_details(original_item['contact'])

    object_model.save()
    return object_model


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=AUTORETRY_EXCEPTIONS,
                 retry_backoff=AUTORETRY_RETRY_BACKOFF, max_retries=RETRY_MAX_RETRIES, retry_backoff_max=AUTORETRY_RETRY_BACKOFF_MAX)
def province_organization_item(self, content_type, raw_item, canonical_iri, cached_path, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']
    try:
        classification = self.source_definition['classification']
    except LookupError as e:
        classification = 'Province'

    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'allmanak',
        'collection': 'province',
        'canonical_iri': canonical_iri,
        'cached_path': cached_path,
    }

    object_model = TopLevelOrganization(original_item['systemid'], **source_defaults)
    object_model.classification = classification
    object_model.collection = self.source_definition['key']
    object_model.name = original_item['naam']
    object_model.description = original_item['omvatplaats']
    object_model.homepage = original_item.get('contact', {}).get('internetadressen', [])[0].get('email')
    object_model.email = original_item.get('contact', {}).get('emailadressen', [])[0].get('url')
    # object_model.contact_details = transform_contact_details(original_item['contact'])

    object_model.save()
    return object_model


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=AUTORETRY_EXCEPTIONS,
                 retry_backoff=AUTORETRY_RETRY_BACKOFF, max_retries=RETRY_MAX_RETRIES, retry_backoff_max=AUTORETRY_RETRY_BACKOFF_MAX)
def party_item(self, content_type, raw_item, canonical_iri, cached_path, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'allmanak',
        'collection': 'party',
        'canonical_iri': canonical_iri,
        'cached_path': cached_path,
    }

    # When the Allmanak implements parties as entities, the canonical_iri should be used
    log.info(original_item)
    if not original_item.get('partij'):
        original_item['partij'] = original_item['naam']
    object_model = Organization(original_item['partij'], **source_defaults)
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
