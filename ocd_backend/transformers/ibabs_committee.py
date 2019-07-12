from ocd_backend.transformers import BaseTransformer
from ocd_backend.models import *


class CommitteeItem(BaseTransformer):
    def transform(self):
        source_defaults = {
            'source': self.source_definition['key'],
            'supplier': 'ibabs',
            'collection': 'committee',
        }

        committee = Organization(self.original_item['Id'],
                                 self.source_definition,
                                 **source_defaults)
        committee.entity = self.entity
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
