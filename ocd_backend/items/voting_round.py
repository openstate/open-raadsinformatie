from datetime import datetime
import iso8601
from pprint import pprint

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

    def _get_result(self):
        if not self.original_item['entry']['ListCanVote']:
            return "Motie aangehouden"
        if self.original_item['entry']['VoteResult']:
            return "Motie aangenomen"
        else:
            return "Motie verworpen"

    def _get_group_results(self, parties):
        if not self.original_item['entry']['ListCanVote']:
            return []
        id2names = dict(list(set(
            [(v['GroupId'], v['GroupName']) for v in self.original_item['votes']])))
        counts = {}
        for v in self.original_item['votes']:
            vote_as_str = "yes" if v['Vote'] else "no"
            try:
                counts[(v['GroupId'], vote_as_str)] += 1
            except KeyError as e:
                counts[(v['GroupId'], vote_as_str)] = 1
        return [{
            "option": group_info[1],
            "value": num_votes,
            "group": {
                "name": id2names[group_info[0]]
            }
        } for group_info, num_votes in counts.iteritems()]

    def _get_counts(self, council, parties, members):
        if not self.original_item['entry']['ListCanVote']:
            return []
        return [
            {
                "option": "yes",
                "value": self.original_item['entry']['VotesInFavour'],
                "group": {
                    "name": "Gemeenteraad"
                }
            },
            {
                "option": "no",
                "value": self.original_item['entry']['VotesAgainst'],
                "group": {
                    "name": "Gemeenteraad"
                }
            }
        ]

    def _get_votes(self, council, parties, members):
        if not self.original_item['entry']['ListCanVote']:
            return []
        return [{'voter_id': v['UserId'], 'option': "yes" if v['Vote'] else "no"} for v in self.original_item['votes']]

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['id'] = self.original_item['motion_id']
        combined_index_data['hidden'] = self.source_definition['hidden']

        council = self._get_council()
        members = self._get_council_members()
        parties = self._get_council_parties()

        combined_index_data['doc'] = {
            "result": self._get_result(),
            "group_results": self._get_group_results(parties),
            "counts": self._get_counts(council, parties, members),
            "votes": self._get_votes(council, parties, members)
        }

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
