from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.models import *
from ocd_backend.transformers import BaseTransformer

log = get_source_logger('notubiz_committee')


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def committee_item(self, content_type, raw_item, canonical_iri, cached_path, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'notubiz',
        'collection': 'committee',
        'canonical_iri': canonical_iri,
    }

    committee = Organization(original_item['id'], **source_defaults)
    committee.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                           source=self.source_definition['key'],
                                                           supplier='allmanak',
                                                           collection=self.source_definition['source_type'])

    committee.name = original_item['title']
    if original_item['title'] == 'Gemeenteraad':
        committee.classification = 'Council'
    else:
        committee.classification = 'Committee'

    committee.subOrganizationOf = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                       source=self.source_definition['key'],
                                                       supplier='allmanak',
                                                       collection=self.source_definition['source_type'])

    committee.save()
    return committee
