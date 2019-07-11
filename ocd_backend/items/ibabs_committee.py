from ocd_backend.items import BaseItem
from ocd_backend.models import *


class CommitteeItem(BaseItem):
    def transform(self):
        source_defaults = {
            'source': self.source_definition['key'],
            'supplier': 'ibabs',
            'collection': 'committee',
        }

        committee = Organization('committee-' + str(self.original_item['Id']), **source_defaults)
        committee.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        committee.has_organization_name.merge(collection=self.source_definition['key'])

        committee.name = self.original_item['Meetingtype']
        committee.description = self.original_item['Abbreviation']

        if 'sub' in self.original_item['Meetingtype']:
            committee.classification = u'Subcommittee'
        else:
            committee.classification = u'Committee'

        # Attach the committee node to the municipality node
        committee.subOrganizationOf = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        committee.subOrganizationOf.merge(collection=self.source_definition['key'])

        return committee
