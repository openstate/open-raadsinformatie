# todo needs revision v1
# from hashlib import sha1
#
# import iso8601
# from ocd_backend.items.popolo import EventItem
#
# from ocd_backend.extractors import HttpRequestMixin
# from ocd_backend.utils.api import FrontendAPIMixin
# from ocd_backend.utils.file_parsing import FileToTextMixin
#
#
# class Meeting(EventItem, HttpRequestMixin, FrontendAPIMixin, FileToTextMixin):
#     def _get_current_permalink(self):
#         return u'%s/meetings/%i' % (self.source_definition[
#                                         'base_url'], self.original_item['id'])
#
#     @staticmethod
#     def _find_meeting_type_id(org):
#         results = [x for x in org['identifiers']
#                    if x['scheme'] == u'GemeenteOplossingen']
#         return results[0]['identifier']
#
#     def _get_committees(self):
#         """
#         Gets the committees that are active for the council.
#         """
#
#         results = self.api_request(
#             self.source_definition['index_name'], 'organizations',
#             classification=['committee', 'subcommittee'])
#         return {self._find_meeting_type_id(c): c for c in results}
#
#     @staticmethod
#     def get_meeting_id(meeting):
#         hash_content = u'meeting-%s' % (meeting['id'])
#         return unicode(sha1(hash_content.decode('utf8')).hexdigest())
#
#     def get_object_id(self):
#         return self.get_meeting_id(self.original_item)
#
#     def get_original_object_id(self):
#         return unicode(self.original_item['id']).strip()
#
#     def get_original_object_urls(self):
#         return {"html": self._get_current_permalink()}
#
#     @staticmethod
#     def get_rights():
#         return u'undefined'
#
#     def get_collection(self):
#         return unicode(self.source_definition['index_name'])
#
#     def get_object_model(self):
#         object_model = {}
#
#         committees = self._get_committees()
#         current_permalink = self._get_current_permalink()
#
#         object_model['id'] = unicode(self.get_object_id())
#
#         object_model['hidden'] = self.source_definition['hidden']
#
#         if self.original_item['description']:
#             object_model['name'] = self.original_item['description']
#         else:
#             object_model['name'] = 'Vergadering %s' % \
#                                    self.original_item['dmu']['name']
#
#         object_model['classification'] = u'Agenda'
#
#         object_model['identifiers'] = [
#             {
#                 'identifier': unicode(self.original_item['id']),
#                 'scheme': u'GemeenteOplossingen'
#             },
#             {
#                 'identifier': self.get_object_id(),
#                 'scheme': u'ORI'
#             }
#         ]
#
#         try:
#             object_model['organization'] = committees[
#                 self.original_item['dmu']['id']]
#         except KeyError:
#             pass
#
#         object_model['organization_id'] = unicode(
#             self.original_item['dmu']['id'])
#
#         object_model['start_date'] = iso8601.parse_date(
#             self.original_item['date'])
#
#         object_model['location'] = self.original_item['location']
#         object_model['status'] = u'confirmed'
#         object_model['sources'] = [
#             {
#                 'url': current_permalink,
#                 'note': u''
#             }
#         ]
#
#         if 'items' in self.original_item:
#             object_model['children'] = [
#                 self.get_meeting_id(mi) for mi in self.original_item['items']]
#
#         object_model['sources'] = []
#
#         try:
#             documents = self.original_item['documents']
#         except KeyError:
#             documents = []
#
#         if documents is None:
#             documents = []
#
#         for document in documents:
#             # sleep(1)
#             url = u"%s/documents/%s" % (current_permalink, document['id'])
#             description = self.file_get_contents(
#                 url,
#                 self.source_definition.get('pdf_max_pages', 20)
#             )
#
#             object_model['sources'].append({
#                 'url': url,
#                 'note': document['filename'],
#                 'description': description
#             })
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
