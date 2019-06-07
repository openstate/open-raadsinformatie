# todo needs revision v1
# from datetime import datetime
#
# import iso8601
# from ocd_backend.items.popolo import (
#     PersonItem, OrganisationItem, MembershipItem)
#
#
# class PopitBaseItem(object):
#     """
#     Base class for importing things from a Popit instance.
#     """
#
#     ignored_list_fields = {
#         'memberships': [
#             # FIXME: start and end dates for memberships borked due to ES configuration (?)
#             'start_date', 'end_date',
#             'url', 'html_url', 'contact_details', 'images', 'links'
#         ],
#         # FIXME: start and end dates for memberships borked due to ES configuration (?)
#         # 'start_date', 'end_date'
#         'area': ['id', 'name']
#     }
#
#     def get_object_id(self):
#         return unicode(self.original_item['id'])
#
#     def get_original_object_id(self):
#         return self.get_object_id()
#
#     def get_original_object_urls(self):
#         try:
#             return self.original_item['meta']['original_object_urls']
#         except KeyError as e:
#             pass
#         try:
#             return {'html': self.original_item['html_url']}
#         except KeyError as e:
#             pass
#         return {}
#
#     def get_rights(self):
#         try:
#             return self.original_item['meta']['rights']
#         except (TypeError, KeyError) as e:
#             return u'undefined'
#
#     def get_object_model(self):
#         object_model = {
#             'hidden': self.source_definition['hidden']
#         }
#
#         for field in self.combined_index_fields:
#             if field not in self.original_item:
#                 continue
#
#             if self.combined_index_fields[field] == unicode:
#                 object_model[field] = unicode(
#                     self.original_item[field])
#             elif self.combined_index_fields[field] == datetime:
#                 if self.original_item[field] is not None:
#                     try:
#                         object_model[field] = iso8601.parse_date(
#                             self.original_item[field])
#                     except iso8601.ParseError as e:
#                         object_model[field] = None
#             elif self.combined_index_fields[field] == list:
#                 if field in self.ignored_list_fields:
#                     object_model[field] = [
#                         {k: v for k, v in l.iteritems() if k not in self.ignored_list_fields[field]} for l in
#                         self.original_item[field]]
#                 else:
#                     object_model[field] = self.original_item[field]
#             elif self.combined_index_fields[field] == dict:
#                 if field in self.ignored_list_fields:
#                     object_model[field] = {
#                         k: v for k, v in self.original_item[field].iteritems() if
#                         k not in self.ignored_list_fields[field]}
#                 else:
#                     object_model[field] = self.original_item[field]
#             else:
#                 object_model[field] = self.original_item[field]
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
#
#
# class PopitPersonItem(PopitBaseItem, PersonItem):
#     """
#     Imports persons from a popit instance.
#     """
#     pass
#
#
# class PopitOrganisationItem(PopitBaseItem, OrganisationItem):
#     """
#     Imports organizations from a popit instance.
#     """
#     pass
#
#
# class PopitMembershipItem(PopitBaseItem, MembershipItem):
#     """
#     Imports a membership from a popit instance.
#     """
#     pass
