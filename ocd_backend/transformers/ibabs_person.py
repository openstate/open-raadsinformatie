import base64

from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.models import *
from ocd_backend.settings import RESOLVER_BASE_URL
from ocd_backend.transformers import BaseTransformer
from ocd_backend.utils.http import GCSCachingMixin

log = get_source_logger('ibabs_person')


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def person_item(self, content_type, raw_item, canonical_iri, cached_path, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']
    
    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'ibabs',
        'cached_path': cached_path,
    }

    person = Person(original_item['UserId'], collection='person', **source_defaults)
    person.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                        source=self.source_definition['key'],
                                                        supplier='allmanak',
                                                        collection=self.source_definition['source_type'])

    person.name = original_item['Name']
    person.family_name = original_item['LastName']
    person.biography = original_item['AboutMe']
    person.email = original_item['Email']
    person.phone = original_item['Phone']

    image = original_item.get('Picture')
    if image:
        path = 'ibabs/image/%s' % original_item['Id']
        GCSCachingMixin.factory('ori-static').upload(path, base64.b64decode(image), content_type='image/jpeg')
        person.image = ImageObject(original_item.get('Id'), collection='image', **source_defaults)
        person.image.content_url = '%s/%s' % (RESOLVER_BASE_URL, path)
        person.image.is_referenced_by = person

    municipality = TopLevelOrganization(self.source_definition['allmanak_id'],
                                        source=self.source_definition['key'],
                                        supplier='allmanak',
                                        collection=self.source_definition['source_type'])

    # The source ID for the municipality membership is constructed by combining the person's iBabs ID and the
    # key of the source
    municipality_membership_id = '%s_%s' % (original_item['UserId'], self.source_definition['key'])
    municipality_member = Membership(municipality_membership_id,
                                     source=self.source_definition['key'],
                                     supplier='ibabs',
                                     collection='municipality_membership')
    municipality_member.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                     source=self.source_definition['key'],
                                                                     supplier='allmanak',
                                                                     collection=self.source_definition['source_type'])

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
                             source=self.source_definition['key'],
                             supplier='ibabs',
                             collection='party')
        party.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                           source=self.source_definition['key'],
                                                           supplier='allmanak',
                                                           collection=self.source_definition['source_type'])

        party.name = original_item['PoliticalPartyName']

        # The source ID for the party membership is constructed by combining the person's iBabs ID and the
        # name of the party
        party_membership_id = '%s_%s' % (original_item['UserId'], original_item['PoliticalPartyName'])
        party_member = Membership(party_membership_id,
                                  source=self.source_definition['key'],
                                  supplier='ibabs',
                                  collection='party_membership')
        party_member.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                  source=self.source_definition['key'],
                                                                  supplier='allmanak',
                                                                  collection=self.source_definition['source_type'])

        party_member.organization = party
        party_member.member = person
        party_member.role = 'Member'

        person.member_of.append(party_member)

    person.save()
    return person
