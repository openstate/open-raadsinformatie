from datetime import datetime
import iso8601

from ocd_backend.items import BaseItem
from ocd_backend.items.popolo import EventItem
from ocd_backend import settings

from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.utils.api import FrontendAPIMixin


class IBabsVotingRoundItem(HttpRequestMixin, FrontendAPIMixin, BaseItem):
    combined_index_fields = {
        'id': unicode,
        'hidden': bool,
        'doc': dict
    }

    def _get_council(self):
        """
        Gets the organisation that represents the council.
        """

        results = self.api_request(
            self.source_definition['index_name'], 'organizations',
            classification='Council')
        return results[0]

    def _get_council_members(self):
        results = self.api_request(self.source_definition['index_name'],
            'persons', size=100)  # 100 for now ...
        return results

    def _get_council_parties(self):
        results = self.api_request(self.source_definition['index_name'],
            'organizations', classification='Party', size=100)  # 100 for now ...
        return results

    def get_object_id(self):
        return unicode(self.original_item['motion_id'])

    def get_original_object_id(self):
        return self.get_object_id()

    def get_original_object_urls(self):
        return {"html": settings.IBABS_WSDL}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['id'] = self.original_item['motion_id']
        combined_index_data['hidden'] = self.source_definition['hidden']

        council = self._get_council()
        members = self._get_council_members()
        parties = self._get_council_parties()

        combined_index_data['doc'] = {
            #'attendees': self._get_voters(vote_event)
        }

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
