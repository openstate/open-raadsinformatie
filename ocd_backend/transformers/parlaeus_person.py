from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.models import *
from ocd_backend.transformers import BaseTransformer

log = get_source_logger('ibabs_person')


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def person_item(self, content_type, raw_item, entity, source_item, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'parlaeus',
        'collection': 'person',
    }

    person = Person(original_item['raid'], **source_defaults)
    person.canonical_id = entity
    person.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                        source=self.source_definition['key'],
                                                        supplier='allmanak',
                                                        collection=self.source_definition['source_type'])

    person.name = original_item['name']

    municipality = TopLevelOrganization(self.source_definition['allmanak_id'],
                                        source=self.source_definition['key'],
                                        supplier='allmanak',
                                        collection=self.source_definition['source_type'])

    # The source ID for the municipality membership is constructed by combining the person's iBabs ID and the
    # key of the source
    municipality_membership_id = '%s_%s' % (original_item['raid'], self.source_definition['key'])
    municipality_member = Membership(municipality_membership_id,
                                     source=self.source_definition['key'],
                                     supplier='parlaeus',
                                     collection='municipality_membership')
    municipality_member.canonical_id = entity
    municipality_member.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                     source=self.source_definition['key'],
                                                                     supplier='allmanak',
                                                                     collection=self.source_definition['source_type'])

    municipality_member.organization = municipality
    municipality_member.member = person

    person.member_of = [municipality_member]

    party = Organization(original_item['party'],
                         source=self.source_definition['key'],
                         supplier='parlaeus',
                         collection='party')
    party.canonical_id = original_item['party']
    party.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                       source=self.source_definition['key'],
                                                       supplier='allmanak',
                                                       collection=self.source_definition['source_type'])

    party.name = original_item['party']

    # The source ID for the party membership is constructed by combining the person's iBabs ID and the
    # name of the party
    party_membership_id = '%s_%s' % (original_item['raid'], original_item['party'])
    party_member = Membership(party_membership_id,
                              source=self.source_definition['key'],
                              supplier='parlaeus',
                              collection='party_membership')
    party_member.canonical_id = entity
    party_member.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                              source=self.source_definition['key'],
                                                              supplier='allmanak',
                                                              collection=self.source_definition['source_type'])

    party_member.organization = party
    party_member.member = person
    party_member.role = original_item['function']

    person.member_of.append(party_member)

    return person
