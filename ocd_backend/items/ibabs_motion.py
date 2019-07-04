# todo needs revision v1
# import re
# from time import sleep
#
# import iso8601
# from ocd_backend.items.popolo import MotionItem, VotingEventItem
#
# from ocd_backend import settings
# from ocd_backend.extractors import HttpRequestMixin
# from ocd_backend.log import get_source_logger
# from ocd_backend.utils.api import FrontendAPIMixin
# from ocd_backend.utils.file_parsing import FileToTextMixin
# from ocd_backend.utils.misc import full_normalized_motion_id
#
# log = get_source_logger('item')
#
#
# class IBabsMotionVotingMixin(HttpRequestMixin, FrontendAPIMixin, FileToTextMixin):
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
#             self.source_definition['index_name'], 'persons', size=100)  # 100
#         return results
#
#     def _get_council_parties(self):
#         results = self.api_request(
#             self.source_definition['index_name'], 'organizations',
#             classification='Party', size=100)  # 100 for now ...
#         return results
#
#     @staticmethod
#     def _get_classification():
#         return u'Moties'
#
#     def _value(self, key):
#         # log.debug(self.source_definition['fields']['Moties'])
#         try:
#             actual_key = self.source_definition[
#                 'fields']['Moties']['Extra'][key]
#         except KeyError:
#             actual_key = key
#         try:
#             return self.original_item['_Extra']['Values'][actual_key]
#         except KeyError:
#             return None
#
#     @staticmethod
#     def _get_creator(creators_str, members, parties):
#         # FIXME: currently only does the first. what do we do with the others?
#         log.debug("Creators: %s" % creators_str)
#
#         if creators_str is None:
#             return
#
#         creator_str = re.split(r'\)[,;]\s*', creators_str)[0]
#         log.debug("Looking for : %s" % (creator_str,))
#
#         party_match = re.search(r' \(([^)]*?)\)?$', creator_str)
#         if not party_match:
#             return
#
#         log.debug("Party match: %s, parties: %s" % (
#             party_match.group(1),
#             u','.join([p.get('name', u'') for p in parties]),))
#         try:
#             party = \
#                 [p for p in parties if unicode(p.get('name', u'')).lower() == unicode(party_match.group(1)).lower()][0]
#         except Exception as e:
#             party = None
#
#         if not party:
#             return
#
#         log.debug("Found party: %s" % (party['name']))
#
#         last_name_match = re.match(r'^([^,]*), ', creator_str)
#         if not last_name_match:
#             return
#
#         last_name_members = [m for m in members if last_name_match.group(1) in m['name']]
#         if len(last_name_members) <= 0:
#             return
#
#         log.debug("Found last name candidates: %s" % (u','.join([m['name'] for m in last_name_members]),))
#
#         if len(last_name_members) == 1:
#             log.debug("Found final candidate base on last name: %s" % (last_name_members[0]['name'],))
#             return last_name_members[0]
#
#         for m in last_name_members:
#             correct_party_affiliations = [ms for ms in m['memberships'] if ms['organization_id'] == party['id']]
#             if len(correct_party_affiliations) > 0:
#                 log.debug("Found final candidate base on last name and party: %s" % (m['name'],))
#                 return m
#
#         return None
#
#     def _find_legislative_session(self, motion_date, council, members, parties):
#         # FIXME: match motions and ev ents when they're closest, not the first you run into
#         motion_day_start = re.sub(r'T\d{2}:\d{2}:\d{2}', 'T00:00:00', motion_date.isoformat())
#         motion_day_end = re.sub(r'T\d{2}:\d{2}:\d{2}', 'T23:59:59', motion_date.isoformat())
#         # log.debug((motion_date.isoformat(), motion_day_start, motion_day_end))
#         try:
#             results = self.api_request(
#                 self.source_definition['index_name'], 'events',
#                 classification=u'Agenda',
#                 start_date={
#                     'from': motion_day_start, 'to': motion_day_end})
#             # log.debug(len(results))
#             # filtered_results = [r for r in results if r['organization_id'] == council['id']]
#             # return filtered_results[0]
#             if results is not None:
#                 return results[0]
#         except (KeyError, IndexError) as e:
#             log.error("Error blaat")
#         return None
#
#     def _get_motion_id_encoded(self):
#         return unicode(
#             full_normalized_motion_id(self._value('Onderwerp')))
#
#     def get_object_id(self):
#         return self._get_motion_id_encoded()
#
#     def get_original_object_id(self):
#         return self._get_motion_id_encoded()
#
#     @staticmethod
#     def get_original_object_urls():
#         # FIXME: what to do when there is not an original URL?
#         return {"html": settings.IBABS_WSDL}
#
#     def _get_motion_data(self, council, members, parties):
#         object_model = dict()
#
#         object_model['id'] = unicode(self.get_original_object_id())
#
#         object_model['hidden'] = self.source_definition['hidden']
#
#         object_model['name'] = unicode(self._value('Onderwerp'))
#
#         object_model['identifier'] = object_model['id']
#
#         object_model['organization_id'] = council['id']
#         object_model['organization'] = council
#
#         # TODO: this gets only the first creator listed. We should fix it to
#         # get all of them
#         creator = self._get_creator(self._value('Indiener(s)'), members, parties)
#         if creator is not None:
#             object_model['creator_id'] = creator['id']
#             object_model['creator'] = creator
#
#         object_model['classification'] = u'Moties'
#
#         object_model['date'] = iso8601.parse_date(self.original_item['datum'][0], )
#         # TODO: this is only for searching compatability ...
#         object_model['start_date'] = object_model['date']
#         object_model['end_date'] = object_model['date']
#
#         # finding the event where this motion was put to a voting round
#         legislative_session = self._find_legislative_session(
#             object_model['date'], council, members, parties)
#         if legislative_session is not None:
#             object_model['legislative_session_id'] = legislative_session['id']
#             object_model['legislative_session'] = legislative_session
#
#         object_model['result'] = self._value('Status')
#         object_model['requirement'] = u'majority'
#         object_model['sources'] = []
#
#         object_model['vote_events'] = [self.get_original_object_id()]
#
#         try:
#             documents = self.original_item['_Extra']['Documents']
#         except KeyError as e:
#             documents = []
#         if documents is None:
#             documents = []
#
#         # Default the text to "-". If a document contains actual text
#         # then that text will be used.
#         object_model['text'] = u"-"
#         for document in documents:
#             sleep(1)
#             log.debug(u"%s: %s" % (
#                 object_model['name'], document['DisplayName'],))
#             description = self.file_get_contents(
#                 public_download_url,
#                 self.source_definition.get('pdf_max_pages', 20)).strip()
#             object_model['sources'].append({
#                 'url': document['PublicDownloadURL'],
#                 'note': document['DisplayName'],
#                 'description': description
#             })
#             # FIXME: assumes that there is only one document from which
#             # we can extract text; is that a valid assumption?
#             if len(description) > 0:
#                 object_model['text'] = description
#
#         return object_model
#
#     def transform(self):
#         council = self._get_council()
#         members = self._get_council_members()
#         parties = self._get_council_parties()
#
#         return self._get_motion_data(council, members, parties)
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
#
#
# class IBabsMotionItem(IBabsMotionVotingMixin, MotionItem):
#     pass
#
#
# class IBabsVoteEventItem(IBabsMotionVotingMixin, VotingEventItem):
#     def transform(self):
#         object_model = {}
#         council = self._get_council()
#         members = self._get_council_members()
#         parties = self._get_council_parties()
#         # log.debug(parties)
#         object_model['motion'] = self._get_motion_data(
#             council, members, parties)
#
#         object_model['classification'] = u'Stemmingen'
#         object_model['hidden'] = self.source_definition['hidden']
#         object_model['start_date'] = object_model['motion']['date']
#         object_model['end_date'] = object_model['motion']['date']
#
#         # we can copy some fields from the motion
#         for field in [
#             'id', 'organization_id', 'organization', 'identifier', 'result',
#             'sources', 'legislative_session_id'
#         ]:
#             try:
#                 object_model[field] = object_model['motion'][field]
#             except KeyError as e:
#                 pass
#
#         # Not all motions are actually voted on
#         # FIXME: are there more. is every municipality specifying the same?
#         # allowed_results = [
#         #     'Motie aangenomen',
#         #     'Motie verworpen',
#         # ]
#
#         object_model['counts'] = []
#         object_model['votes'] = []
#
#         # if object_model['result'] not in allowed_results:
#         #     return object_model
#         #
#         # party_ids = [p['id'] for p in parties if p.has_key('id')]
#         #
#         # # make the vote a bit random, but retain te result by majority vote
#         # majority_count = (len(members) // 2) + 1
#         # vote_count_to_result = len(members)
#         # new_vote_count_to_result = vote_count_to_result
#         # current_votes = {p['id']: object_model['result'] for p in parties if p.has_key('name')}
#         # party_sizes = {p['id']: len(list(set([m['person_id'] for m in p['memberships']]))) for p in parties if p.has_key('name')}
#         # parties_voted = []
#         #
#         # while new_vote_count_to_result >= majority_count:
#         #     if new_vote_count_to_result != vote_count_to_result:
#         #         vote_count_to_result = new_vote_count_to_result
#         #         current_votes[party_id] = random.choice([r for r in allowed_results if r != object_model['result']])
#         #         parties_voted.append(party_id)
#         #
#         #     # pick a random party
#         #     party_id = random.choice([p for p in party_ids if p not in parties_voted])
#         #
#         #     new_vote_count_to_result = new_vote_count_to_result - party_sizes[party_id]
#         #
#         # # now record the votes
#         # for party in parties:
#         #     if not party.has_key('name'):
#         #         continue
#         #     try:
#         #         num_members = len(list(set([m['person_id'] for m in party['memberships']])))
#         #     except KeyError as e:
#         #         num_members = 0
#         #     object_model['counts'].append({
#         #         'option': current_votes[party['id']],  # object_model['result'],
#         #         'value': num_members,
#         #         'group': {
#         #             'name': party.get('name', '')
#         #         }
#         #     })
#         #
#         # # FIXME: get the actual individual votes, depends on the voting kind
#         # for m in members:
#         #     try:
#         #         member_party = [ms['organization_id'] for ms in m['memberships'] if ms['organization_id'] in party_ids][0]
#         #         member_vote = current_votes[member_party]
#         #     except (KeyError, IndexError) as e:
#         #         member_party = None
#         #         member_vote = object_model['result']
#         #
#         #     object_model['votes'].append({
#         #         'voter_id' : m['id'],
#         #         'voter': m,
#         #         'option': member_vote,  # FIXME: actual vote
#         #         'group_id': member_party
#         #     })
#
#         return object_model
