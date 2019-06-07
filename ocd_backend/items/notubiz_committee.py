from ocd_backend.items import BaseItem
from ocd_backend.models import *


class CommitteeItem(BaseItem):
    def get_rights(self):
        return u'undefined'

    def get_object_model(self):
        source_defaults = {
            'source': 'notubiz',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        committee = Organization(self.original_item['id'], **source_defaults)
        committee.has_organization_name = TopLevelOrganization(self.source_definition['key'], *source_defaults)
        committee.has_organization_name.merge(collection=self.source_definition['key'])

        committee.name = self.original_item['title']
        if self.original_item['title'] == 'Gemeenteraad':
            committee.classification = 'Council'
        else:
            committee.classification = 'Committee'

        # Attach the committee node to the municipality node
        committee.subOrganizationOf = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        committee.subOrganizationOf.merge(collection=self.source_definition['key'])

        return committee
