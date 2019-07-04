from ocd_backend.items import BaseItem
from ocd_backend.models import *


class CommitteeItem(BaseItem):
    def transform(self):
        source_defaults = {
            'source': 'notubiz',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        committee = Organization('committee-' + str(self.original_item['id']), **source_defaults)
        committee.has_organization_name = TopLevelOrganization(self.source_definition['key'], *source_defaults)
        # TODO: Merge

        committee.name = self.original_item['title']
        if self.original_item['title'] == 'Gemeenteraad':
            committee.classification = 'Council'
        else:
            committee.classification = 'Committee'

        # Attach the committee node to the municipality node
        committee.subOrganizationOf = TopLevelOrganization(self.source_definition['key'], **source_defaults)

        return committee
