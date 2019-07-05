from ocd_backend.items import BaseItem
from ocd_backend.models import *
from ocd_backend.log import get_source_logger

log = get_source_logger('persons')


class AllmanakPersonItem(BaseItem):
    def transform(self):
        source_defaults = {
            'source': 'allmanak',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        person = Person(self.original_item['systemid'], **source_defaults)
        person.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        person.has_organization_name.merge(collection=self.source_definition['key'])

        person.name = self.original_item['naam']
        if 'Dhr.' in self.original_item['naam']:
            person.gender = 'Man'
        elif 'Mw.' in self.original_item['naam']:
            person.gender = 'Vrouw'

        municipality = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        municipality.merge(collection=self.source_definition['key'])

        # The source ID for the municipality membership is constructed by combining the person's Allmanak ID and the
        # key of the source
        municipality_membership_id = '%s_%s' % (self.original_item['systemid'], self.source_definition['key'])
        municipality_member = Membership(municipality_membership_id, **source_defaults)
        municipality_member.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        municipality_member.has_organization_name.merge(collection=self.source_definition['key'])

        municipality_member.organization = municipality
        municipality_member.member = person
        municipality_member.role = 'Raadslid'

        person.member_of = [municipality_member]

        if self.original_item['partij']:
            party = Organization(self.original_item['partij'], **source_defaults)
            party.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
            party.has_organization_name.merge(collection=self.source_definition['key'])

            party.name = self.original_item['partij']

            # The source ID for the party membership is constructed by combining the person's Allmanak ID and the
            # name of the party
            party_membership_id = '%s_%s' % (self.original_item['systemid'], self.original_item['partij'])
            party_member = Membership(party_membership_id, **source_defaults)
            party_member.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
            party_member.has_organization_name.merge(collection=self.source_definition['key'])

            party_member.organization = party
            party_member.member = person
            party_member.role = 'Lid'

            person.member_of.append(party_member)

        return person
