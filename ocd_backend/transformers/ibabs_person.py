from ocd_backend import celery_app
from ocd_backend.transformers import BaseTransformer
from ocd_backend.models import *
from ocd_backend.log import get_source_logger

log = get_source_logger('ibabs_person')


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=(Exception,), retry_backoff=True)
def person_item(self, content_type, raw_item, entity, source_item, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    source_definition = kwargs['source_definition']
    
    source_defaults = {
        'source': source_definition['key'],
        'supplier': 'ibabs',
        'collection': 'person',
    }

    person = Person(original_item['UserId'],
                    source_definition,
                    **source_defaults)
    person.entity = entity
    person.has_organization_name = TopLevelOrganization(source_definition['allmanak_id'],
                                                        source=source_definition['key'],
                                                        supplier='allmanak',
                                                        collection='municipality')

    person.name = original_item['Name']
    person.family_name = original_item['LastName']
    person.biography = original_item['AboutMe']
    person.email = original_item['Email']
    person.phone = original_item['Phone']

    municipality = TopLevelOrganization(source_definition['allmanak_id'],
                                        source=source_definition['key'],
                                        supplier='allmanak',
                                        collection='municipality')

    # The source ID for the municipality membership is constructed by combining the person's iBabs ID and the
    # key of the source
    municipality_membership_id = '%s_%s' % (original_item['UserId'], source_definition['key'])
    municipality_member = Membership(municipality_membership_id,
                                     source_definition,
                                     source=source_definition['key'],
                                     supplier='ibabs',
                                     collection='municipality_membership')
    municipality_member.entity = entity
    municipality_member.has_organization_name = TopLevelOrganization(source_definition['allmanak_id'],
                                                                     source=source_definition['key'],
                                                                     supplier='allmanak',
                                                                     collection='municipality')

    municipality_member.organization = municipality
    municipality_member.member = person

    # FunctionName is often set to 'None' in the source, in that case we fall back to 'Member'
    if original_item['FunctionName'] == 'None':
        municipality_member.role = 'Member'
    else:
        municipality_member.role = original_item['FunctionName']

    person.member_of = [municipality_member]

    if original_item['PoliticalPartyId']:
        # Currently there is no way to merge parties from the Allmanak with parties from ibabs because
        # they do not share any consistent identifiers, so new nodes will be created for parties that ibabs
        # persons are linked to. This causes ibabs sources that have persons to have duplicate party nodes.
        # These duplicate nodes are necessary to cover ibabs sources that have no persons, otherwise those
        # sources would not have any parties.
        party = Organization(original_item['PoliticalPartyId'],
                             source_definition,
                             source=source_definition['key'],
                             supplier='ibabs',
                             collection='party')
        party.entity = original_item['PoliticalPartyId']
        party.has_organization_name = TopLevelOrganization(source_definition['allmanak_id'],
                                                           source=source_definition['key'],
                                                           supplier='allmanak',
                                                           collection='municipality')

        party.name = original_item['PoliticalPartyName']

        # The source ID for the party membership is constructed by combining the person's iBabs ID and the
        # name of the party
        party_membership_id = '%s_%s' % (original_item['UserId'], original_item['PoliticalPartyName'])
        party_member = Membership(party_membership_id,
                                  source_definition,
                                  source=source_definition['key'],
                                  supplier='ibabs',
                                  collection='party_membership')
        party_member.entity = entity
        party_member.has_organization_name = TopLevelOrganization(source_definition['allmanak_id'],
                                                                  source=source_definition['key'],
                                                                  supplier='allmanak',
                                                                  collection='municipality')

        party_member.organization = party
        party_member.member = person
        party_member.role = 'Member'

        person.member_of.append(party_member)

    person.save()
    return person
