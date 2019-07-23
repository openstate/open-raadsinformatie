from ocd_backend import celery_app
from ocd_backend.transformers import BaseTransformer
from ocd_backend.models import *
from ocd_backend.log import get_source_logger

log = get_source_logger('persons')


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=(Exception,), retry_backoff=True)
def allmanak_person_item(self, content_type, raw_item, entity, source_item, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    source_definition = kwargs['source_definition']
    
    source_defaults = {
        'source': source_definition['key'],
        'supplier': 'allmanak',
        'collection': 'person',
    }

    person = Person(original_item['systemid'],
                    source_definition,
                    **source_defaults)
    person.entity = entity
    person.has_organization_name = TopLevelOrganization(source_definition['allmanak_id'],
                                                        source=source_definition['key'],
                                                        supplier='allmanak',
                                                        collection='muncipality')

    person.name = original_item['naam']
    if 'Dhr.' in original_item['naam']:
        person.gender = 'Man'
    elif 'Mw.' in original_item['naam']:
        person.gender = 'Vrouw'

    municipality = TopLevelOrganization(source_definition['allmanak_id'],
                                        source=source_definition['key'],
                                        supplier='allmanak',
                                        collection='muncipality')

    # The source ID for the municipality membership is constructed by combining the person's Allmanak ID and the
    # key of the source
    municipality_membership_id = '%s_%s' % (original_item['systemid'], source_definition['key'])
    municipality_member = Membership(municipality_membership_id,
                                     source_definition,
                                     source=source_definition['key'],
                                     supplier='allmanak',
                                     collection='municipality_membership')
    municipality_member.entity = entity
    municipality_member.has_organization_name = TopLevelOrganization(source_definition['allmanak_id'],
                                                                     source=source_definition['key'],
                                                                     supplier='allmanak',
                                                                     collection='muncipality')

    municipality_member.organization = municipality
    municipality_member.member = person
    municipality_member.role = 'Raadslid'

    person.member_of = [municipality_member]

    if original_item['partij']:
        party = Organization(original_item['partij'],
                             source=source_definition['key'],
                             supplier='allmanak',
                             collection='party')
        party.merge(collection=source_definition['key'] + '-' + original_item['partij'])
        party.has_organization_name = TopLevelOrganization(source_definition['allmanak_id'],
                                                           source=source_definition['key'],
                                                           supplier='allmanak',
                                                           collection='muncipality')

        party.name = original_item['partij']

        # The source ID for the party membership is constructed by combining the person's Allmanak ID and the
        # name of the party
        party_membership_id = '%s_%s' % (original_item['systemid'], original_item['partij'])
        party_member = Membership(party_membership_id,
                                  source_definition,
                                  source=source_definition['key'],
                                  supplier='allmanak',
                                  collection='party_membership')
        party_member.entity = entity
        party_member.has_organization_name = TopLevelOrganization(source_definition['allmanak_id'],
                                                                  source=source_definition['key'],
                                                                  supplier='allmanak',
                                                                  collection='muncipality')

        party_member.organization = party
        party_member.member = person
        party_member.role = 'Lid'

        person.member_of.append(party_member)

    person.save()
    return person
