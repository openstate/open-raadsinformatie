from ocd_backend.items import BaseItem
from ocd_backend.models import *


class IbabsPerson(BaseItem):
    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        source_defaults = {
            'source': 'notubiz',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        # Todo more properties can be extracted

        person = Person(self.original_item['UserId'], **source_defaults)
        person.name = self.original_item['Name']
        person.family_name = self.original_item['LastName']
        person.biography = self.original_item['AboutMe']
        person.email = self.original_item['Email']
        person.phone = self.original_item['Phone']

        municipality = Organization(self.source_definition['almanak_id'], **source_defaults)
        municipality.name = self.source_definition['sitename']

        municipality_member = Membership(**source_defaults)
        municipality_member.organization = municipality
        municipality_member.role = self.original_item['FunctionName']

        person.member_of = [municipality_member]

        if self.original_item['PoliticalPartyId']:
            party = Organization(self.original_item['PoliticalPartyId'], **source_defaults)
            party.name = self.original_item['PoliticalPartyName']

            party_member = Membership(**source_defaults)
            party_member.organization = party
            party_member.role = 'Member'

            person.member_of.append(party_member)

        return person
