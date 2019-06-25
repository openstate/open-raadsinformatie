from ocd_backend.items import BaseItem
from ocd_backend.models import *


class CommitteeItem(BaseItem):
    def get_object_model(self):
        source_defaults = {
            'source': 'gemeenteoplossingen',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        committee = Organization('committee-' + str(self.original_item['id']), **source_defaults)
        committee.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)

        committee.name = self.original_item['name']
        if self.original_item['name'] == 'Gemeenteraad':
            committee.classification = 'Council'
        else:
            committee.classification = 'Committee'

        committee.subOrganizationOf = TopLevelOrganization(self.source_definition['key'], **source_defaults)

        return committee
