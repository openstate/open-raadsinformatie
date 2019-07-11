from ocd_backend.items import BaseItem
from ocd_backend.models import *


class IbabsPersonItem(BaseItem):
    def transform(self):
        source_defaults = {
            'source': self.source_definition['key'],
            'supplier': 'ibabs',
            'collection': 'person',
        }

        person = Person(self.original_item['UserId'],
                        self.source_definition,
                        **source_defaults)
        person.entity = self.entity
        person.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        person.has_organization_name.merge(collection=self.source_definition['key'])

        person.name = self.original_item['Name']
        person.family_name = self.original_item['LastName']
        person.biography = self.original_item['AboutMe']
        person.email = self.original_item['Email']
        person.phone = self.original_item['Phone']

        municipality = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        municipality.merge(collection=self.source_definition['key'])

        # The source ID for the municipality membership is constructed by combining the person's iBabs ID and the
        # key of the source
        municipality_membership_id = '%s_%s' % (self.original_item['UserId'], self.source_definition['key'])
        municipality_member = Membership(municipality_membership_id,
                                         self.source_definition,
                                         source=self.source_definition['key'],
                                         supplier='ibabs',
                                         collection='person_municipality_membership')
        municipality_member.entity = self.entity
        municipality_member.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        municipality_member.has_organization_name.merge(collection=self.source_definition['key'])

        municipality_member.organization = municipality
        municipality_member.member = person

        # FunctionName is often set to 'None' in the source, in that case we fall back to 'Member'
        if self.original_item['FunctionName'] == 'None':
            municipality_member.role = 'Member'
        else:
            municipality_member.role = self.original_item['FunctionName']

        person.member_of = [municipality_member]

        if self.original_item['PoliticalPartyId']:
            # Currently there is no way to merge parties from the Allmanak with parties from ibabs because
            # they do not share any consistent identifiers, so new nodes will be created for parties that ibabs
            # persons are linked to. This causes ibabs sources that have persons to have duplicate party nodes.
            # These duplicate nodes are necessary to cover ibabs sources that have no persons, otherwise those
            # sources would not have any parties.
            party = Organization(self.original_item['PoliticalPartyId'],
                                 self.source_definition,
                                 source=self.source_definition['key'],
                                 supplier='ibabs',
                                 collection='party')
            party.entity = self.original_item['PoliticalPartyId']
            party.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
            party.has_organization_name.merge(collection=self.source_definition['key'])

            party.name = self.original_item['PoliticalPartyName']

            # The source ID for the party membership is constructed by combining the person's iBabs ID and the
            # name of the party
            party_membership_id = '%s_%s' % (self.original_item['UserId'], self.original_item['PoliticalPartyName'])
            party_member = Membership(party_membership_id,
                                      self.source_definition,
                                      source=self.source_definition['key'],
                                      supplier='ibabs',
                                      collection='person_party_membership')
            party_member.entity = self.entity
            party_member.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
            party_member.has_organization_name.merge(collection=self.source_definition['key'])

            party_member.organization = party
            party_member.member = person
            party_member.role = 'Member'

            person.member_of.append(party_member)

        return person
