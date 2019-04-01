# todo needs revision v1
# from hashlib import sha1
#
# from ocd_backend.items.popolo import OrganisationItem
#
#
# class GemeenteOplossingenCommittee(OrganisationItem):
#     def _get_current_permalink(self):
#         return u'%s/dmus' % (self.source_definition['base_url'])
#
#     @staticmethod
#     def _get_meeting_id(meeting):
#         hash_content = u'committee-%s' % (meeting['id'])
#         return sha1(hash_content.decode('utf8')).hexdigest()
#
#     def get_object_id(self):
#         return self._get_meeting_id(self.original_item)
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
#         object_model = dict()
#
#         object_model['id'] = unicode(self.get_object_id())
#
#         object_model['hidden'] = self.source_definition['hidden']
#         object_model['name'] = unicode(self.original_item['name'])
#         object_model['identifiers'] = [
#             {
#                 'identifier': self.get_object_id(),
#                 'scheme': u'ORI'
#             },
#             {
#                 'identifier': self.original_item['id'],
#                 'scheme': u'GemeenteOplossingen'
#             }
#         ]
#
#         object_model['classification'] = u'committee'
#         object_model['description'] = object_model['name']
#
#         object_model['sources'] = [
#             {
#                 'url': self._get_current_permalink(),
#                 'note': u''
#             }
#         ]
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
