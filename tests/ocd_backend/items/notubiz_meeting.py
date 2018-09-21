import json
import os

import iso8601
from mock import MagicMock
from ocd_backend.items import BaseItem
from ocd_backend.items.notubiz_meeting import NotubizMeeting
from ocd_backend.models import Meeting
from ocd_backend.utils.file_parsing import FileToTextMixin
from ocd_backend.models.serializers import Neo4jSerializer, RdfSerializer, JsonLDSerializer, JsonSerializer
from ocd_backend.models.database import Neo4jDatabase
from ocd_backend.models.model import Model
from ocd_backend import celery_app

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

        self.db = Neo4jDatabase(Neo4jSerializer())
        self.cleanup_neo4j()

        celery_app.backend.remove("ori_identifier_autoincrement")

        with open(dump_path, 'r') as f:
            self.raw_item = f.read()

        self.meeting = json.loads(self.raw_item)

        self.meeting_ins = self._instantiate_meeting()

        jsonld_serializer = JsonLDSerializer()
        self.jsonld_data = jsonld_serializer.serialize(self.meeting_ins.object_data)

        json_serializer = JsonSerializer()
        self.json_data = json_serializer.serialize(self.meeting_ins.object_data)

        self.expected_jsonld = {
            'ori_identifier': 'https://id.openraadsinformatie.nl/1',
            'status': 'https://argu.co/ns/meeting/EventConfirmed',
            'name': u'raadscommissie Financi\xebn',
            'classification': [u'Agenda'],
            'had_primary_source': u'https://argu.co/voc/mapping/amsterdam/notubiz/identifier/458902',
            '@type': 'Meeting',
            'attachment': [
                'https://id.openraadsinformatie.nl/3',
                'https://id.openraadsinformatie.nl/4'
            ],
            'agenda': [
                'https://id.openraadsinformatie.nl/5',
                'https://id.openraadsinformatie.nl/6',
                'https://id.openraadsinformatie.nl/7',
                'https://id.openraadsinformatie.nl/8',
                'https://id.openraadsinformatie.nl/9',
                'https://id.openraadsinformatie.nl/10',
                'https://id.openraadsinformatie.nl/11',
                'https://id.openraadsinformatie.nl/12',
                'https://id.openraadsinformatie.nl/13',
                'https://id.openraadsinformatie.nl/14',
                'https://id.openraadsinformatie.nl/15',
                'https://id.openraadsinformatie.nl/16',
                'https://id.openraadsinformatie.nl/17',
                'https://id.openraadsinformatie.nl/18',
                'https://id.openraadsinformatie.nl/19',
                'https://id.openraadsinformatie.nl/20',
                'https://id.openraadsinformatie.nl/21',
                'https://id.openraadsinformatie.nl/22',
                'https://id.openraadsinformatie.nl/23',
                'https://id.openraadsinformatie.nl/24',
                'https://id.openraadsinformatie.nl/25',
                'https://id.openraadsinformatie.nl/26',
                'https://id.openraadsinformatie.nl/27',
                'https://id.openraadsinformatie.nl/28',
                'https://id.openraadsinformatie.nl/29',
                'https://id.openraadsinformatie.nl/30',
                'https://id.openraadsinformatie.nl/31',
                'https://id.openraadsinformatie.nl/32',
                'https://id.openraadsinformatie.nl/33',
                'https://id.openraadsinformatie.nl/34',
                'https://id.openraadsinformatie.nl/35',
                'https://id.openraadsinformatie.nl/36',
                'https://id.openraadsinformatie.nl/37',
                'https://id.openraadsinformatie.nl/38',
                'https://id.openraadsinformatie.nl/39',
                'https://id.openraadsinformatie.nl/40',
                'https://id.openraadsinformatie.nl/41',
                'https://id.openraadsinformatie.nl/42',
                'https://id.openraadsinformatie.nl/43'
            ],
            '@context': {
                'status': {'@id': 'http://schema.org/eventStatus', '@type': '@id'},
                'name': {'@id': 'http://schema.org/name'},
                'classification': {'@id': 'http://www.semanticdesktop.org/ontologies/2007/04/02/ncal#categories'},
                'had_primary_source': {'@id': 'http://www.w3.org/ns/prov#hadPrimarySource'},
                '@base': 'https://id.openraadsinformatie.nl/',
                'attachment': {'@id': 'https://argu.co/ns/meeting/attachment', '@type': '@id'},
                'agenda': {'@id': 'https://argu.co/ns/meeting/agenda', '@type': '@id'},
                'organization': {'@id': 'http://schema.org/organizer', '@type': '@id'},
                'Meeting': 'https://argu.co/ns/meeting/Meeting',
                'start_date': {'@id': 'http://schema.org/startDate'},
                'committee': {'@id': 'https://argu.co/ns/meeting/committee', '@type': '@id'}
            },
            'organization': 'https://id.openraadsinformatie.nl/45',
            'start_date': '2018-02-08T13:30:00+01:00',
            'committee': 'https://id.openraadsinformatie.nl/44'
        }

        self.expected_json = {
            'ori_identifier': 'https://id.openraadsinformatie.nl/1',
            'status': 'https://argu.co/ns/meeting/EventConfirmed',
            'name': u'raadscommissie Financi\xebn',
            'classification': [u'Agenda'],
            'had_primary_source': u'https://argu.co/voc/mapping/amsterdam/notubiz/identifier/458902',
            'attachment': [
                'https://id.openraadsinformatie.nl/3',
                'https://id.openraadsinformatie.nl/4'
            ],
            'agenda': [
                'https://id.openraadsinformatie.nl/5',
                'https://id.openraadsinformatie.nl/6',
                'https://id.openraadsinformatie.nl/7',
                'https://id.openraadsinformatie.nl/8',
                'https://id.openraadsinformatie.nl/9',
                'https://id.openraadsinformatie.nl/10',
                'https://id.openraadsinformatie.nl/11',
                'https://id.openraadsinformatie.nl/12',
                'https://id.openraadsinformatie.nl/13',
                'https://id.openraadsinformatie.nl/14',
                'https://id.openraadsinformatie.nl/15',
                'https://id.openraadsinformatie.nl/16',
                'https://id.openraadsinformatie.nl/17',
                'https://id.openraadsinformatie.nl/18',
                'https://id.openraadsinformatie.nl/19',
                'https://id.openraadsinformatie.nl/20',
                'https://id.openraadsinformatie.nl/21',
                'https://id.openraadsinformatie.nl/22',
                'https://id.openraadsinformatie.nl/23',
                'https://id.openraadsinformatie.nl/24',
                'https://id.openraadsinformatie.nl/25',
                'https://id.openraadsinformatie.nl/26',
                'https://id.openraadsinformatie.nl/27',
                'https://id.openraadsinformatie.nl/28',
                'https://id.openraadsinformatie.nl/29',
                'https://id.openraadsinformatie.nl/30',
                'https://id.openraadsinformatie.nl/31',
                'https://id.openraadsinformatie.nl/32',
                'https://id.openraadsinformatie.nl/33',
                'https://id.openraadsinformatie.nl/34',
                'https://id.openraadsinformatie.nl/35',
                'https://id.openraadsinformatie.nl/36',
                'https://id.openraadsinformatie.nl/37',
                'https://id.openraadsinformatie.nl/38',
                'https://id.openraadsinformatie.nl/39',
                'https://id.openraadsinformatie.nl/40',
                'https://id.openraadsinformatie.nl/41',
                'https://id.openraadsinformatie.nl/42',
                'https://id.openraadsinformatie.nl/43'
            ],
            'organization': 'https://id.openraadsinformatie.nl/45',
            'start_date': '2018-02-08T13:30:00+01:00',
            'committee': 'https://id.openraadsinformatie.nl/44'
        }

        self.rights = u'undefined'  # for now ...
        self.collection = u'amsterdam'

    def tearDown(self):
        self.cleanup_neo4j()

    def cleanup_neo4j(self):
        self.db.query('MATCH (n) DETACH DELETE n')

    def _instantiate_meeting(self):
        """
        Instantiate the item from the raw and parsed item we have
        """
        meeting = NotubizMeeting(self.source_definition, 'application/json', self.raw_item, self.meeting, None)
        return meeting

    def test_meeting_get_ori_id(self):
        self.assertEqual('https://id.openraadsinformatie.nl/1', self.meeting_ins.object_data.get_ori_identifier())

    def test_meeting_get_rights(self):
        item = self._instantiate_meeting()
        self.assertEqual(self.rights, item.get_rights())

    def test_meeting_get_collection(self):
        item = self._instantiate_meeting()
        self.assertEqual(self.collection, item.get_collection())

    def test_meeting_json(self):
        for name, _ in Meeting.definitions(props=True, rels=True):
            self.assertEqual(self.expected_json.get(name), self.json_data.get(name))

    def test_meeting_jsonld(self):
        for name, _ in Meeting.definitions(props=True, rels=True):
            self.assertEqual(self.expected_jsonld.get(name), self.jsonld_data.get(name))
