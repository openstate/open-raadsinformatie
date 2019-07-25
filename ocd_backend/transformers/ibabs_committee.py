from ocd_backend import celery_app
from ocd_backend.transformers import BaseTransformer
from ocd_backend.models import *
from ocd_backend.log import get_source_logger

log = get_source_logger('ibabs_committee')


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=(Exception,), retry_backoff=True)
def committee_item(self, content_type, raw_item, entity, source_item, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    source_definition = kwargs['source_definition']

    source_defaults = {
        'source': source_definition['key'],
        'supplier': 'ibabs',
        'collection': 'committee',
    }

    committee = Organization(original_item['Id'],
                             source_definition,
                             **source_defaults)
    committee.entity = entity
    committee.has_organization_name = TopLevelOrganization(source_definition['allmanak_id'],
                                                           source=source_definition['key'],
                                                           supplier='allmanak',
                                                           collection=source_definition['source_type'])

    committee.name = original_item['Meetingtype']
    committee.description = original_item['Abbreviation']

    if 'sub' in original_item['Meetingtype']:
        committee.classification = u'Subcommittee'
    else:
        committee.classification = u'Committee'

    # Attach the committee node to the municipality node
    committee.subOrganizationOf = TopLevelOrganization(source_definition['allmanak_id'],
                                                       source=source_definition['key'],
                                                       supplier='allmanak',
                                                       collection=source_definition['source_type'])

    committee.save()
    return committee
