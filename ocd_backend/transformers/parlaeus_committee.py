from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.models import *
from ocd_backend.transformers import BaseTransformer


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def committee_item(self, content_type, raw_item, entity, source_item, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'parlaeus',
        'collection': 'committee',
    }

    committee = Organization(original_item['Id'], **source_defaults)
    committee.canonical_id = entity
    committee.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                           source=self.source_definition['key'],
                                                           supplier='allmanak',
                                                           collection=self.source_definition['source_type'])

    committee.name = original_item['committeename']
    committee.other_names = original_item['committeecode']
    committee.classification = u'Committee'

    return committee
