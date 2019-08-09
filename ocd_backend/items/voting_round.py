# todo needs revision v1
# from ocd_backend import settings
# from ocd_backend.extractors import HttpRequestMixin
# from ocd_backend.items import BaseItem
# from ocd_backend.utils.api import FrontendAPIMixin
# from ocd_backend.utils.misc import full_normalized_motion_id
#
#
# class IBabsVotingRoundItem(HttpRequestMixin, FrontendAPIMixin, BaseItem):
#     combined_index_fields = {
#         'id': unicode,
#         'hidden': bool,
#         'doc': dict
#     }
#
#     def _get_council(self):
#         """
#         Gets the organisation that represents the council.
#         """
#
#         results = self.api_request(
#             self.source_definition['index_name'], 'organizations',
#             classification='Council')
#         return results[0]
#
#     def _get_council_members(self):
#         results = self.api_request(
#             self.source_definition['index_name'], 'persons',
#             size=100)  # 100 for now ...
#         return results
#
#     def _get_council_parties(self):
#         results = self.api_request(
#             self.source_definition['index_name'], 'organizations',
#             classification='Party', size=100)  # 100 for now
#         return results
#
#     def get_object_id(self):
#         return unicode(full_normalized_motion_id(
#             self.original_item['entry']['EntryTitle']))
#
#     def get_original_object_id(self):
#         return self.get_object_id()
#
#     @staticmethod
#     def get_original_object_urls():
#         return {"html": settings.IBABS_WSDL}
#
#     def _get_result(self):
#         if not self.original_item['entry']['ListCanVote']:
#             return "Motie aangehouden"
#         if self.original_item['entry']['VoteResult']:
#             return "Motie aangenomen"
#         else:
#             return "Motie verworpen"
#
#     def _get_group_results(self, parties):
#         if not self.original_item['entry']['ListCanVote']:
#             return []
#         id2names = dict(list(set(
#             [(v['GroupId'], v['GroupName']) for v in self.original_item['votes']])))
#         counts = {}
#         for v in self.original_item['votes']:
#             vote_as_str = "yes" if v['Vote'] else "no"
#             try:
#                 counts[(v['GroupId'], vote_as_str)] += 1
#             except KeyError as e:
#                 counts[(v['GroupId'], vote_as_str)] = 1
#         return [{
#             "option": group_info[1],
#             "value": num_votes,
#             "group_id": group_info[0],
#             "group": {
#                 "name": id2names[group_info[0]]
#             }
#         } for group_info, num_votes in counts.iteritems()]
#
#     def _get_counts(self, council, parties, members):
#         if not self.original_item['entry']['ListCanVote']:
#             return []
#         return [
#             {
#                 "option": "yes",
#                 "value": self.original_item['entry']['VotesInFavour'],
#                 "group": {
#                     "name": "Gemeenteraad"
#                 }
#             },
#             {
#                 "option": "no",
#                 "value": self.original_item['entry']['VotesAgainst'],
#                 "group": {
#                     "name": "Gemeenteraad"
#                 }
#             }
#         ]
#
#     def _get_votes(self, council, parties, members):
#         if not self.original_item['entry']['ListCanVote']:
#             return []
#
#         members_by_id = {m['id']: {'name': m['name']} for m in members}
#         return [{
#             'voter_id': v['UserId'],
#             'voter': members_by_id.get(v['UserId'], None),
#             'group_id': v['GroupId'],
#             'option': "yes" if v['Vote'] else "no"
#         } for v in self.original_item['votes']]
#
#     def get_object_model(self):
#         object_model = dict()
#
#         object_model['id'] = self.original_item['motion_id']
#         object_model['hidden'] = self.source_definition['hidden']
#
#         council = self._get_council()
#         members = self._get_council_members()
#         parties = self._get_council_parties()
#
#         object_model['doc'] = {
#             "result": self._get_result(),
#             "group_results": self._get_group_results(parties),
#             "counts": self._get_counts(council, parties, members),
#             "votes": self._get_votes(council, parties, members)
#         }
#
#         return object_model
#
#     @staticmethod
#     def get_index_data():
#         return {}
#
#     @staticmethod
#     def get_all_text():
#         text_items = []
#
#         return u' '.join(text_items)
