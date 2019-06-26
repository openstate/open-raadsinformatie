# TODO: Rewrite for Postgres

# import json
# import os
# 
# from ocd_backend import celery_app
# from ocd_backend.items.notubiz_meeting import NotubizMeetingItem
# from ocd_backend.models import Meeting
# from ocd_backend.models.serializers import JsonLDSerializer, JsonSerializer
# from . import ItemTestCase
#
#
# class NotubizMeetingTestCase(ItemTestCase):
#     def setUp(self):
#         self.PWD = os.path.dirname(__file__)
#         dump_path = os.path.abspath(os.path.join(self.PWD, '../test_dumps/notubiz_meeting_amsterdam.json'))
#
#         self.source_definition = {
#             'organisation_id': 281,
#             'keep_index_on_update': True,
#             'enrichers': [['ocd_backend.enrichers.media_enricher.static.local_static_media_enricher', None]],
#             'cleanup': 'ocd_backend.tasks.cleanup_elasticsearch',
#             'doc_type': 'events',
#             'sitename': 'Amsterdam',
#             'municipality': 'Amsterdam',
#             'id': 'amsterdam_meetings',
#             'index_name': 'amsterdam',
#             'base_url': 'https://api.notubiz.nl',
#             'entity': 'meetings',
#             'extractor': 'ocd_backend.extractors.notubiz.NotubizMeetingExtractor',
#             'key': 'amsterdam',
#             'wait_until_finished': True,
#             'hidden': False,
#             'loader': 'ocd_backend.loaders.elasticsearch.elasticsearch_loader',
#             'item': 'ocd_backend.items.notubiz_meeting.Meeting',
#         }
#
#         self.db = Neo4jDatabase(Neo4jSerializer())
#         self.cleanup_neo4j()
#
#         celery_app.backend.remove("ori_identifier_autoincrement")
#
#         with open(dump_path, 'r') as f:
#             self.raw_item = f.read()
#
#         self.meeting = json.loads(self.raw_item)
#
#         self.meeting_ins = self._instantiate_meeting()
#
#         jsonld_serializer = JsonLDSerializer()
#         self.jsonld_data = jsonld_serializer.serialize(self.meeting_ins.object_data)
#
#         json_serializer = JsonSerializer()
#         self.json_data = json_serializer.serialize(self.meeting_ins.object_data)
#
#         self.expected_jsonld = {
#             'ori_identifier': 'https://id.openraadsinformatie.nl/1',
#             'status': 'https://argu.co/ns/meeting/EventConfirmed',
#             'name': u'raadscommissie Financi\xebn',
#             'has_organization_name': '3',
#             'classification': [u'Agenda'],
#             'had_primary_source': u'https://argu.co/voc/mapping/amsterdam/notubiz/identifier/458902',
#             '@type': 'Meeting',
#             'attachment': ['4', '5'],
#             'agenda': {
#                 '@list': ['6', '7', '8', '9', '10', '11', '13', '15', '21', '23', '24', '25', '26', '27', '28',
#                           '31', '34', '35', '38', '41', '42', '43', '44', '47', '52', '53', '56', '59', '62', '65',
#                           '70', '73', '77', '78', '81', '82', '86', '89', '93']
#             },
#             '@context': {
#                 'status': {'@id': 'http://schema.org/eventStatus', '@type': '@id'},
#                 'name': {'@id': 'http://schema.org/name'},
#                 'has_organization_name': {'@id': 'http://www.w3.org/2006/vcard/ns#hasOrganizationName', '@type': '@id'},
#                 'classification': {'@id': 'http://www.semanticdesktop.org/ontologies/2007/04/02/ncal#categories'},
#                 'had_primary_source': {'@id': 'http://www.w3.org/ns/prov#hadPrimarySource'},
#                 '@base': 'https://id.openraadsinformatie.nl/',
#                 'attachment': {'@id': 'https://argu.co/ns/meeting/attachment', '@type': '@id'},
#                 'agenda': {'@id': 'https://argu.co/ns/meeting/agenda', '@type': '@id'},
#                 'organization': {'@id': 'http://schema.org/organizer', '@type': '@id'},
#                 'Meeting': 'https://argu.co/ns/meeting/Meeting',
#                 'start_date': {'@id': 'http://schema.org/startDate'},
#                 'committee': {'@id': 'https://argu.co/ns/meeting/committee', '@type': '@id'}
#             },
#             'organization': '3',
#             'start_date': '2018-02-08T13:30:00+01:00',
#             'committee': '94'
#         }
#
#         self.expected_json = {
#             'ori_identifier': 'https://id.openraadsinformatie.nl/1',
#             'status': 'https://argu.co/ns/meeting/EventConfirmed',
#             'name': u'raadscommissie Financi\xebn',
#             'has_organization_name': 'https://id.openraadsinformatie.nl/3',
#             'classification': [u'Agenda'],
#             'had_primary_source': u'https://argu.co/voc/mapping/amsterdam/notubiz/identifier/458902',
#             'attachment': [
#                 'https://id.openraadsinformatie.nl/4',
#                 'https://id.openraadsinformatie.nl/5'
#             ],
#             'agenda': ['https://id.openraadsinformatie.nl/6',
#                        'https://id.openraadsinformatie.nl/7',
#                        'https://id.openraadsinformatie.nl/8',
#                        'https://id.openraadsinformatie.nl/9',
#                        'https://id.openraadsinformatie.nl/10',
#                        'https://id.openraadsinformatie.nl/11',
#                        'https://id.openraadsinformatie.nl/13',
#                        'https://id.openraadsinformatie.nl/15',
#                        'https://id.openraadsinformatie.nl/21',
#                        'https://id.openraadsinformatie.nl/23',
#                        'https://id.openraadsinformatie.nl/24',
#                        'https://id.openraadsinformatie.nl/25',
#                        'https://id.openraadsinformatie.nl/26',
#                        'https://id.openraadsinformatie.nl/27',
#                        'https://id.openraadsinformatie.nl/28',
#                        'https://id.openraadsinformatie.nl/31',
#                        'https://id.openraadsinformatie.nl/34',
#                        'https://id.openraadsinformatie.nl/35',
#                        'https://id.openraadsinformatie.nl/38',
#                        'https://id.openraadsinformatie.nl/41',
#                        'https://id.openraadsinformatie.nl/42',
#                        'https://id.openraadsinformatie.nl/43',
#                        'https://id.openraadsinformatie.nl/44',
#                        'https://id.openraadsinformatie.nl/47',
#                        'https://id.openraadsinformatie.nl/52',
#                        'https://id.openraadsinformatie.nl/53',
#                        'https://id.openraadsinformatie.nl/56',
#                        'https://id.openraadsinformatie.nl/59',
#                        'https://id.openraadsinformatie.nl/62',
#                        'https://id.openraadsinformatie.nl/65',
#                        'https://id.openraadsinformatie.nl/70',
#                        'https://id.openraadsinformatie.nl/73',
#                        'https://id.openraadsinformatie.nl/77',
#                        'https://id.openraadsinformatie.nl/78',
#                        'https://id.openraadsinformatie.nl/81',
#                        'https://id.openraadsinformatie.nl/82',
#                        'https://id.openraadsinformatie.nl/86',
#                        'https://id.openraadsinformatie.nl/89',
#                        'https://id.openraadsinformatie.nl/93'],
#             'organization': 'https://id.openraadsinformatie.nl/3',
#             'start_date': '2018-02-08T13:30:00+01:00',
#             'committee': 'https://id.openraadsinformatie.nl/94'
#         }
#
#         self.rights = u'undefined'  # for now ...
#         self.collection = u'amsterdam'
#
#     def tearDown(self):
#         self.cleanup_neo4j()
#
#     def cleanup_neo4j(self):
#         self.db.query('MATCH (n) DETACH DELETE n')
#
#     def _instantiate_meeting(self):
#         """
#         Instantiate the item from the raw and parsed item we have
#         """
#         meeting = NotubizMeetingItem(self.source_definition, 'application/json', self.raw_item, self.meeting, None)
#         return meeting
#
#     def test_meeting_get_ori_id(self):
#         self.assertEqual('https://id.openraadsinformatie.nl/1', self.meeting_ins.object_data.get_ori_identifier())
#
#     def test_meeting_json(self):
#         for name, _ in Meeting.definitions(props=True, rels=True):
#             self.assertEqual(self.expected_json.get(name), self.json_data.get(name))
#
#     def test_meeting_jsonld(self):
#         for name, _ in Meeting.definitions(props=True, rels=True):
#             self.assertEqual(self.expected_jsonld.get(name), self.jsonld_data.get(name))
