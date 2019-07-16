from ocd_backend import celery_app
from ocd_backend.transformers import BaseTransformer
from ocd_backend.models import *
from ocd_backend.log import get_source_logger

log = get_source_logger('goapi_committee')


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=(Exception,), retry_backoff=True)
def committee_item(self, content_type, raw_item, entity, source_item, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    source_definition = kwargs['source_definition']
    
    source_defaults = {
        'source': source_definition['key'],
        'supplier': 'gemeenteoplossingen',
        'collection': 'committee',
    }

    committee = Organization(original_item['id'],
                             source_definition,
                             **source_defaults)
    committee.entity = entity
    committee.has_organization_name = TopLevelOrganization(source_definition['allmanak_id'],
                                                           source=source_definition['key'],
                                                           supplier='allmanak',
                                                           collection='governmental_organization')

    committee.name = original_item['name']
    if original_item['name'] == 'Gemeenteraad':
        committee.classification = 'Council'
    else:
        committee.classification = 'Committee'

    committee.subOrganizationOf = TopLevelOrganization(source_definition['allmanak_id'],
                                                       source=source_definition['key'],
                                                       supplier='allmanak',
                                                       collection='governmental_organization')

    committee.save()
    return committee
