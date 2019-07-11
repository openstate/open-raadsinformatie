from ocd_backend.items import BaseItem
from ocd_backend.models import *


class CommitteeItem(BaseItem):
    def transform(self):
        source_defaults = {
            'source': self.source_definition['key'],
            'supplier': 'gemeenteoplossingen',
            'collection': 'committee',
        }

        committee = Organization(self.original_item['id'],
                                 self.source_definition,
                                 **source_defaults)
        committee.entity = self.entity
        committee.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        committee.has_organization_name.merge(collection=self.source_definition['key'])

        committee.name = self.original_item['name']
        if self.original_item['name'] == 'Gemeenteraad':
            committee.classification = 'Council'
        else:
            committee.classification = 'Committee'

        committee.subOrganizationOf = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        committee.subOrganizationOf.merge(collection=self.source_definition['key'])

        return committee
