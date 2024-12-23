from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.models import *
from ocd_backend.transformers import BaseTransformer
from ocd_backend.settings import AUTORETRY_EXCEPTIONS, RETRY_MAX_RETRIES, AUTORETRY_RETRY_BACKOFF, AUTORETRY_RETRY_BACKOFF_MAX

log = get_source_logger('persons')


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=AUTORETRY_EXCEPTIONS,
                 retry_backoff=AUTORETRY_RETRY_BACKOFF, max_retries=RETRY_MAX_RETRIES, retry_backoff_max=AUTORETRY_RETRY_BACKOFF_MAX)
def allmanak_person_item(self, content_type, raw_item, canonical_iri, cached_path, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']
    
    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'allmanak',
        'collection': 'person',
        'canonical_iri': canonical_iri,
        'cached_path': cached_path,
    }

    person = Person(original_item['systemid'], **source_defaults)
    person.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                        source=self.source_definition['key'],
                                                        supplier='allmanak',
                                                        collection=self.source_definition['source_type'])

    person.name = original_item['naam']
    if 'Dhr.' in original_item['naam']:
        person.gender = 'Man'
    elif 'Mw.' in original_item['naam']:
        person.gender = 'Vrouw'

    municipality = TopLevelOrganization(self.source_definition['allmanak_id'],
                                        source=self.source_definition['key'],
                                        supplier='allmanak',
                                        collection=self.source_definition['source_type'])

    # The source ID for the municipality membership is constructed by combining the person's Allmanak ID and the
    # key of the source
    municipality_membership_id = '%s_%s' % (original_item['systemid'], self.source_definition['key'])
    municipality_member = Membership(municipality_membership_id,
                                     source=self.source_definition['key'],
                                     supplier='allmanak',
                                     collection='municipality_membership')

    municipality_member.has_organization_name = municipality
    municipality_member.organization = municipality

    municipality_member.member = person
    municipality_member.role = 'Raadslid'

    person.member_of = [municipality_member]

    if original_item['partij']:
        party = Organization(original_item['partij'],
                             source=self.source_definition['key'],
                             supplier='allmanak',
                             collection='party',
                             merge_into=('collection',
                                         'prop_string',
                                         self.source_definition['key'] + '-' + original_item['partij']))
        party.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                           source=self.source_definition['key'],
                                                           supplier='allmanak',
                                                           collection=self.source_definition['source_type'])

        party.name = original_item['partij']

        # The source ID for the party membership is constructed by combining the person's Allmanak ID and the
        # name of the party
        party_membership_id = '%s_%s' % (original_item['systemid'], original_item['partij'])
        party_member = Membership(party_membership_id,
                                  source=self.source_definition['key'],
                                  supplier='allmanak',
                                  collection='party_membership')
        party_member.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                  source=self.source_definition['key'],
                                                                  supplier='allmanak',
                                                                  collection=self.source_definition['source_type'])

        party_member.organization = party
        party_member.member = person
        party_member.role = 'Lid'

        person.member_of.append(party_member)

    person.save()
    return person
