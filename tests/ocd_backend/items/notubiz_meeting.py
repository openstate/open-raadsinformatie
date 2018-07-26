import json
import os

import iso8601
from mock import MagicMock
from ocd_backend.items import BaseItem
from ocd_backend.items.notubiz_meeting import NotubizMeeting
from ocd_backend.models import Meeting
from ocd_backend.utils.file_parsing import FileToTextMixin
from ocd_backend.models.serializers import RdfSerializer, JsonLDSerializer, JsonSerializer

from . import ItemTestCase


class NotubizMeetingTestCase(ItemTestCase):
    def setUp(self):
        self.PWD = os.path.dirname(__file__)
        dump_path = os.path.abspath(os.path.join(self.PWD, '../test_dumps/notubiz_meeting_amsterdam.json'))

        self.source_definition = {
            'organisation_id': 281,
            'keep_index_on_update': True,
            'enrichers': [['ocd_backend.enrichers.media_enricher.static.StaticMediaEnricher', None]],
            'cleanup': 'ocd_backend.tasks.CleanupElasticsearch',
            'doc_type': 'events',
            'sitename': 'Amsterdam',
            'municipality': 'Amsterdam',
            'id': 'amsterdam_meetings',
            'index_name': 'amsterdam',
            'base_url': 'https://api.notubiz.nl',
            'entity': 'meetings',
            'extractor': 'ocd_backend.extractors.notubiz.NotubizMeetingExtractor',
            'key': 'amsterdam',
            'wait_until_finished': True,
            'hidden': False,
            'loader': 'ocd_backend.loaders.ElasticsearchLoader',
            'item': 'ocd_backend.items.notubiz_meeting.Meeting',
        }

        with open(dump_path, 'r') as f:
            self.raw_item = f.read()

        self.meeting = json.loads(self.raw_item)

        self.model = self._instantiate_meeting().get_object_model()
        self.model.save()

        jsonld_serializer = JsonLDSerializer()
        jsonld_data = jsonld_serializer.serialize(self.model)

        json_serializer = JsonSerializer()
        json_data = json_serializer.serialize(self.model)

        self.namespaced_data = self.model.deflate(namespaces=True, props=True, rels=True)
        self.not_namespaced_data = self.model.deflate(namespaces=False, props=True, rels=True)

        self.expected_namespaced_result = {
            'schema:name': u'Vergadering raadscommissie Financi\xebn 2018-02-08 13:30:00',
            'govid:notubizIdentifier': u'458902',
            'schema:eventStatus': 'council:EventConfirmed',
            'ncal:categories': [u'Agenda'],
            'schema:startDate': 1518093000,
            'govid:oriIdentifier': u'47f08ad2e44e564f765169f338857d939897be79',
            'schema:organizer': u'a91e0157bcfe56548f8e8082c5ffe1a5ac9a1288',
            'council:committee': u'43b0e0f2e1bcc2304c422dbe4abec9d74fb364eb',
            'council:attachment': [
                {
                    'schema:isBasedOn': u'https://api.notubiz.nl/document/6183601/1',
                    'schema:name': u'Uitslagenlijst FIN 2018 02 08',
                    'govid:notubizIdentifier': u'6183601',
                    'govid:oriIdentifier': u'2528bd4c4467ed8a93925848ec2f937166c24857'
                },
                {
                    'schema:isBasedOn': u'https://api.notubiz.nl/document/6268204/1',
                    'schema:name': u'Definitief verslag FIN 08 02 2018',
                    'govid:notubizIdentifier': u'6268204',
                    'govid:oriIdentifier': u'f744bca176b6c070cf1374b87e33a6fac51d4d86'
                }
            ],
            'council:agenda': [
                u'e5f2f4f712281d690311ec0cd0614e411188017b', u'56df75c7cc3fb119500c1016741fc0f1ba6c5ee7',
                u'09e848100805196bc7ed348e4bc84eb45ba1c827', u'f100ee0951dd4e311da2e1ef5efd83e6bb858275',
                u'5df248a5da6148107142e228c784ce5b6a3ea3b4', u'e41d4b52f7f030deebe3c47ecffd532c13020f5d',
                u'e7afd12481c30adb7c25fef43c67451a81f10094', u'4db6aec6e9ddc06066eae5b296a224bcf8aed2ce',
                u'cb1d9364fe465dc4f9638875634f19bc6f54ec9b', u'26b551181db84082e18eef92e33589986d51a9cd',
                u'a110be2d58eef40b15b3267199e149292e317a60', u'dd4ebac9b95d5f94f27395c91b0e264c21cc26dd',
                u'69318c050b5c237a4b7140118d3344ca3ffeced6', u'3320040a19e87a07cc9fe66ae7284c339b1b2eab',
                u'688bd4549f9f6913ee5ef5d41e4f5befdc282164', u'26874b6e0659e149fe7a00721a39a49a7d699822',
                u'e2dae2f6eb79950a7d6cd4a352fe166daf743f2c', u'1b70c5a5c76623b5c897b2196285e9e1b9a8dba7',
                u'ee09e29199f84d5eca7b5478ef057e021ba41d94', u'10338f01c6fdbd7cf249b5c3e893c563090bdb2b',
                u'b3d9b5854f848913a38af8d5178635a9fea110f0', u'e8f0d3ffa695558a5f32f29b9f78203071539cb3',
                u'1f1e55a5e57e4897120c3d2030a3f8fbc7e342b6', u'04d64d024623ef8019b5ce7118ca59d7671e48b0',
                u'3c8fca623a7e4df055ab876ad0b61e156f6e3d2d', u'fa28b59306bad33eb0195e15ab7001ed583b9744',
                u'56b87763f8e0f4652af204af2c08b3391d0d5b33', u'938d52bdbafebb7a208f06c9734ccf2731ad1c32',
                u'f370ffac0c3cfb3d6c6e2e4fbadb22680b104ee8', u'f6d736886ea43f009542717ef56587015a4ec46a',
                u'3f27bd8df2c88ad51c6df0eb69d84022e9c72fc5', u'702980f3322957375859030558d67cd80e7402b7',
                u'b425dfcadff8b7d716d3f05cfceb748d5b7f7863', u'84d58d430815b921439fe5b9b43fd62e8dddf2ab',
                u'b51654a3f0dcaadbf003fa6b5168fdc0c68b823a', u'0bcb5f00554f6db86b10da1f7d4126975f383402',
                u'e9be65e049b83a58c704976303fd1b308144b52d', u'40f9627c2e1c8aa53d097d115f13018ade514515',
                u'826ae256c61962aa1aed67d5ba4ecaf3654d4a74'
            ],
        }

        self.expected_not_namespaced_result = {
            'status': 'council:EventConfirmed',
            'name': u'Vergadering raadscommissie Financi\xebn 2018-02-08 13:30:00',
            'classification': [u'Agenda'],
            'ori_identifier': u'47f08ad2e44e564f765169f338857d939897be79',
            'notubiz_identifier': u'458902',
            'start_date': 1518093000,
            'committee': u'43b0e0f2e1bcc2304c422dbe4abec9d74fb364eb',
            'organization': u'a91e0157bcfe56548f8e8082c5ffe1a5ac9a1288',
            'attachment': [
                {
                    'original_url': u'https://api.notubiz.nl/document/6183601/1',
                    'name': u'Uitslagenlijst FIN 2018 02 08',
                    'notubiz_identifier': u'6183601',
                    'ori_identifier': u'2528bd4c4467ed8a93925848ec2f937166c24857'
                },
                {
                    'original_url': u'https://api.notubiz.nl/document/6268204/1',
                    'name': u'Definitief verslag FIN 08 02 2018',
                    'notubiz_identifier': u'6268204',
                    'ori_identifier': u'f744bca176b6c070cf1374b87e33a6fac51d4d86'
                }
            ],
            'agenda': [
                u'e5f2f4f712281d690311ec0cd0614e411188017b', u'56df75c7cc3fb119500c1016741fc0f1ba6c5ee7',
                u'09e848100805196bc7ed348e4bc84eb45ba1c827', u'f100ee0951dd4e311da2e1ef5efd83e6bb858275',
                u'5df248a5da6148107142e228c784ce5b6a3ea3b4', u'e41d4b52f7f030deebe3c47ecffd532c13020f5d',
                u'e7afd12481c30adb7c25fef43c67451a81f10094', u'4db6aec6e9ddc06066eae5b296a224bcf8aed2ce',
                u'cb1d9364fe465dc4f9638875634f19bc6f54ec9b', u'26b551181db84082e18eef92e33589986d51a9cd',
                u'a110be2d58eef40b15b3267199e149292e317a60', u'dd4ebac9b95d5f94f27395c91b0e264c21cc26dd',
                u'69318c050b5c237a4b7140118d3344ca3ffeced6', u'3320040a19e87a07cc9fe66ae7284c339b1b2eab',
                u'688bd4549f9f6913ee5ef5d41e4f5befdc282164', u'26874b6e0659e149fe7a00721a39a49a7d699822',
                u'e2dae2f6eb79950a7d6cd4a352fe166daf743f2c', u'1b70c5a5c76623b5c897b2196285e9e1b9a8dba7',
                u'ee09e29199f84d5eca7b5478ef057e021ba41d94', u'10338f01c6fdbd7cf249b5c3e893c563090bdb2b',
                u'b3d9b5854f848913a38af8d5178635a9fea110f0', u'e8f0d3ffa695558a5f32f29b9f78203071539cb3',
                u'1f1e55a5e57e4897120c3d2030a3f8fbc7e342b6', u'04d64d024623ef8019b5ce7118ca59d7671e48b0',
                u'3c8fca623a7e4df055ab876ad0b61e156f6e3d2d', u'fa28b59306bad33eb0195e15ab7001ed583b9744',
                u'56b87763f8e0f4652af204af2c08b3391d0d5b33', u'938d52bdbafebb7a208f06c9734ccf2731ad1c32',
                u'f370ffac0c3cfb3d6c6e2e4fbadb22680b104ee8', u'f6d736886ea43f009542717ef56587015a4ec46a',
                u'3f27bd8df2c88ad51c6df0eb69d84022e9c72fc5', u'702980f3322957375859030558d67cd80e7402b7',
                u'b425dfcadff8b7d716d3f05cfceb748d5b7f7863', u'84d58d430815b921439fe5b9b43fd62e8dddf2ab',
                u'b51654a3f0dcaadbf003fa6b5168fdc0c68b823a', u'0bcb5f00554f6db86b10da1f7d4126975f383402',
                u'e9be65e049b83a58c704976303fd1b308144b52d', u'40f9627c2e1c8aa53d097d115f13018ade514515',
                u'826ae256c61962aa1aed67d5ba4ecaf3654d4a74'],
        }

        self.rights = u'undefined'  # for now ...
        self.collection = u'amsterdam'

    def _instantiate_meeting(self):
        """
        Instantiate the item from the raw and parsed item we have
        """
        return NotubizMeeting(self.source_definition, 'application/json', self.raw_item, self.meeting, None)

    def test_meeting_get_ori_id(self):
        self.assertEqual(self.model.get_ori_id(), self.expected_namespaced_result.get('govid:oriIdentifier'))

    def test_meeting_get_rights(self):
        item = self._instantiate_meeting()
        self.assertEqual(item.get_rights(), self.rights)

    def test_meeting_get_collection(self):
        item = self._instantiate_meeting()
        self.assertEqual(item.get_collection(), self.collection)

    def test_meeting_values_with_namespace(self):
        for _, prop in Meeting.definitions(props=True, rels=True):
            full_name = prop.get_prefix_uri()
            self.assertEqual(self.namespaced_data.get(full_name), self.expected_namespaced_result.get(full_name))

    def test_meeting_values_without_namespace(self):
        for name, _ in Meeting.definitions(props=True, rels=True):
            self.assertEqual(self.not_namespaced_data.get(name), self.expected_not_namespaced_result.get(name))
