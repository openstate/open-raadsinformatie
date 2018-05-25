from ocd_backend.items import BaseItem
from ocd_backend.models import *


class CommitteeItem(BaseItem):
    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        committee = Organization('ibabs_identifier', self.original_item['Id'])
        committee.name = self.original_item['Meetingtype']

        if 'sub' in self.original_item['Meetingtype']:
            committee.classification = u'subcommittee'
        else:
            committee.classification = u'committee'
        committee.description = self.original_item['Abbreviation']

        return committee
