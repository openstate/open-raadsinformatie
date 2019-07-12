# todo needs revision v1
# import iso8601
#
# from ocd_backend.extractors import HttpRequestMixin
# from ocd_backend.utils.api import FrontendAPIMixin
# from ocd_backend.utils.file_parsing import FileToTextMixin
#
#
# class VideotulenItem(EventItem, HttpRequestMixin, FrontendAPIMixin, FileToTextMixin):
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
#     def _get_committees(self):
#         """
#         Gets the committees that are active for the council.
#         """
#
#         results = self.api_request(
#             self.source_definition['index_name'], 'organizations',
#             classification=['committee', 'subcommittee'])
#         return {unicode(c['name']): c for c in results}
#
#     def get_original_object_id(self):
#         return unicode(self.original_item['Webcast']['Id']).strip()
#
#     def get_original_object_urls(self):
#         return {"html": unicode(self.original_item['Webcast']['RegisterUrl']).strip()}
#
#     def transform(self):
#         object_model = {}
#         council = self._get_council()
#         committees = self._get_committees()
#
#         object_model['id'] = unicode(self.get_object_id())
#
#         object_model['hidden'] = self.source_definition['hidden']
#
#         if 'Title' in self.original_item['Webcast']:
#             object_model['name'] = u'%s' % (
#                 unicode(self.original_item['Webcast']['Title']),)
#         else:
#             object_model['name'] = self.source_definition['key']
#
#         object_model['identifiers'] = [
#             {
#                 'identifier': unicode(self.original_item['Webcast']['Id']),
#                 'scheme': u'CWC'
#             },
#             {
#                 'identifier': self.get_object_id(),
#                 'scheme': u'ORI'
#             }
#         ]
#
#         try:
#             object_model['organization_id'] = committees[
#                 object_model['name']]['id']
#             object_model['organization'] = committees[
#                 object_model['name']]
#         except KeyError as e:
#             object_model['organization_id'] = council['id']
#             object_model['organization'] = council
#
#         object_model['classification'] = u'Videotulen %s' % (
#             object_model['name'],)
#
#         topic_descriptions = []
#         if self.original_item['Webcast']['Topics'] is not None:
#             for topic in self.original_item['Webcast']['Topics']['Topic']:
#                 topic_description = topic.get('Description')
#                 if topic_description is None:
#                     topic_description = u''
#                 topic_descriptions.append(
#                     u'<h3>%s</h3>\n<p>%s</p>' % (
#                         topic['Title'], topic_description,))
#
#         if len(topic_descriptions) > 0:
#             object_model['description'] = u'\n'.join(topic_descriptions)
#         else:
#             object_model['description'] = self.original_item['Webcast']['Description']
#
#         if 'ActualStart' in self.original_item['Webcast']:
#             start_date_field = 'ActualStart'
#             end_date_field = 'ActualEnd'
#         else:
#             start_date_field = 'ScheduledStart'
#             end_date_field = 'ScheduledStart'
#
#         object_model['start_date'] = iso8601.parse_date(
#             self.original_item['Webcast'][start_date_field], )
#         object_model['end_date'] = iso8601.parse_date(
#             self.original_item['Webcast'][end_date_field], )
#         object_model['location'] = u'Raadszaal'
#         object_model['status'] = u'confirmed'
#
#         object_model['sources'] = [
#             {'url': a['Location'], 'note': a['Description']} for a in
#             self.original_item['Webcast']['Attachments']['Attachment']]
#
#         documents = []
#         if self.original_item['Webcast']['Topics'] is not None:
#             for topic in self.original_item['Webcast']['Topics']['Topic']:
#                 if topic['Attachments'] is None:
#                     continue
#                 for a in topic['Attachments']['Attachment']:
#                     try:
#                         description = self.file_get_contents(
#                             a['Location'],
#                             self.source_definition.get('pdf_max_pages', 20))
#                     except Exception as e:
#                         description = u''
#                     documents.append({
#                         'url': a['Location'], 'note': a['Description'],
#                         'description': description})
#         object_model['sources'] += documents
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
