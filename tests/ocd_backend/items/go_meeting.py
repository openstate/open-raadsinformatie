import json
import os
from mock import MagicMock
from pprint import pprint

from lxml import etree
import iso8601

from ocd_backend.items.go_meeting import MeetingItem

from . import ItemTestCase


class MeetingItemTestCase(ItemTestCase):
    def setUp(self):
        super(MeetingItemTestCase, self).setUp()
        self.PWD = os.path.dirname(__file__)
        dump_path = os.path.abspath(os.path.join(self.PWD, '../test_dumps/den_helder_meeting.html'))
        dump_item_path = os.path.abspath(os.path.join(self.PWD, '../test_dumps/den_helder_meeting_item.html'))
        dump_item_docs_path = os.path.abspath(os.path.join(self.PWD, '../test_dumps/den_helder_meeting_item_documents.html'))

        faulty_path = os.path.abspath(os.path.join(self.PWD, '../test_dumps/den_helder_faulty_meeting.html'))
        faulty_item_path = os.path.abspath(os.path.join(self.PWD, '../test_dumps/den_helder_faulty_meeting_item.html'))

        self.source_definition = {
            'id': 'test_definition',
            'extractor': 'ocd_backend.extractors.staticfile.StaticJSONDumpExtractor',
            'transformer': 'ocd_backend.transformers.BaseTransformer',
            'item': 'ocd_backend.items.go_meeting.MeetingItem',
            'loader': 'ocd_backend.loaders.ElasticsearchLoader',
            'hidden': False,
            'index_name': 'den_helder'
        }

        with open(dump_path, 'r') as f:
            self.raw_item = f.read()

        with open(dump_item_path, 'r') as f:
            self.raw_meeting_item = f.read()

        self.docs_raw_item = u''
        with open(dump_item_docs_path, 'r') as f:
            self.docs_raw_item = f.read()

        with open(faulty_path, 'r') as f:
            self.raw_faulty_item = f.read()

        with open(faulty_item_path, 'r') as f:
            self.raw_faulty_meeting_item = f.read()

        self.meeting = {
            'type': 'meeting',
            'content': self.raw_item,
            'full_content': self.raw_item
        }

        self.meeting_item = {
            'type': 'meeting-item',
            'content': self.raw_meeting_item,
            'full_content': self.raw_item
        }

        self.meeting_object_id = u'https://gemeenteraad.denhelder.nl/Vergaderingen/Gemeenteraad/2015/31-augustus/19:30/'
        self.meeting_item_object_id = u'https://gemeenteraad.denhelder.nl/Vergaderingen/Gemeenteraad/2015/31-augustus/19:30/#agendapunt19024_4718'
        self.meeting_object_urls = {
            'html': u'https://gemeenteraad.denhelder.nl/Vergaderingen/Gemeenteraad/2015/31-augustus/19:30/'
        }
        self.meeting_item_object_urls = {
            'html': u'https://gemeenteraad.denhelder.nl/Vergaderingen/Gemeenteraad/2015/31-augustus/19:30/#agendapunt19024_4718'
        }
        self.rights = u'undefined' # for now ...
        self.collection = u'Gemeenteraad 31 augustus 2015 19:30:00'

        self.meeting_name = u'Gemeenteraad 31 augustus 2015 19:30:00'
        self.meeting_item_name = u'6. Bekrachtigen van de geheimhouding op de daartoe door het college gewaarmerkte exploitatie  van Zeestad per 1 januari 2015.'

        self.meeting_identifiers = [
            {
                'identifier': u'https://gemeenteraad.denhelder.nl/Vergaderingen/Gemeenteraad/2015/31-augustus/19:30/',
                'scheme': u'GemeenteOplossingen'
            },
            {
                'identifier': '99cae907404739fad9570d577bf9852391e4fd7b',
                'scheme': u'ORI'
            }
        ]

        self.meeting_item_identifiers = [
            {
                'scheme': u'GemeenteOplossingen',
                'identifier': u'https://gemeenteraad.denhelder.nl/Vergaderingen/Gemeenteraad/2015/31-augustus/19:30/#agendapunt19024_4718'
            },
            {
                'scheme': u'ORI',
                'identifier': '94d1cd4c80286b0125910a9508a40eebc9358387'
            }
        ]
        self.meeting_classification = u'Meeting'
        self.meeting_item_classification = u'Meeting Item'

        self.start_date = iso8601.parse_date(u'2015-08-31T19:30:00')
        self.location = u'Gemeentehuis'
        self.status = u'confirmed'

        self.children = [
            u'd6a63d2d6c597fa34836b35578be792d9e600f4b',
            u'2006ef27c94d5c84140eae9cfff15ca2b851f89f',
            u'1e814e3f7c4724a4ed20f30ba60fb9e94930725f',
            u'2006ef27c94d5c84140eae9cfff15ca2b851f89f',
            u'ae4914eeb2288e8622ee950ef125f2a8e4827d78',
            u'2006ef27c94d5c84140eae9cfff15ca2b851f89f',
            u'2006ef27c94d5c84140eae9cfff15ca2b851f89f',
            u'2006ef27c94d5c84140eae9cfff15ca2b851f89f',
            u'2006ef27c94d5c84140eae9cfff15ca2b851f89f',
            u'2006ef27c94d5c84140eae9cfff15ca2b851f89f',
            u'2006ef27c94d5c84140eae9cfff15ca2b851f89f',
            u'2006ef27c94d5c84140eae9cfff15ca2b851f89f',
            u'6e0c293ea8a00331d0e8ec7b1a4fdfeadd0dde36',
            u'6da707660b7f9021ace5fccedacbe9dda8da9b0e',
            u'ce331fc7ff9db647664173137ab5e15fcff50935'
        ]

        self.meeting_sources = [
            {
                'note': u'Oproep vergadering gemeenteraad.pdf',
                'url': u'https://gemeenteraad.denhelder.nl/Vergaderingen/Gemeenteraad/2015/31-augustus/Oproep-vergadering-gemeenteraad-7.pdf'
            },
            {
                'note': u'1. 2015-08-31-19-01-19-Gemeenteraad.mp3',
                'url': u'https://gemeenteraad.denhelder.nl/Vergaderingen/Gemeenteraad/2015/31-augustus/19:30/download/888/mp3'
            }
        ]

        self.meeting_item_sources = [
            {
                'note': u'Raadsbesluit bekrachtiging geheimhouding Exploitatie Zeestad..pdf',
                'url': u'https://gemeenteraad.denhelder.nl/Documenten/Raadsbesluit-bekrachtiging-geheimhouding-Exploitatie-Zeestad.pdf'
            }
        ]

        self.organisation = {'id': u'1', 'name': u'Den Helder'}

        self.meeting_description = u''
        self.meeting_item_description = u'Het college van burgemeester en wethouders heeft onder geheimhouding stukken ter inzage gelegd over de exploitatie van Zeestad. Op grond van artikel 25, lid 3, van de Gemeentewet dient de raad de geheimhouding te bekrachtigen.'

        self.faulty_meeting_item_id = u'18612'
        self.faulty_meeting_item_documents_url = u'https://gemeenteraad.denhelder.nl/modules/risbis/risbis.php?g=get_docs_for_ag&agendapunt_object_id=18612'

    def _instantiate_meeting(self):
        """
        Instantiate the item from the raw and parsed item we have
        """

        # # FIXME: these need to return some values
        MeetingItem._get_council = MagicMock(return_value={'id': u'1', 'name': u'Den Helder'})
        MeetingItem._get_committees = MagicMock(return_value={})
        MeetingItem._get_documents_html_for_item = MagicMock(return_value=self.docs_raw_item)

        item = MeetingItem(
            self.source_definition, 'application/json',
            self.raw_item, self.meeting
        )



        return item

    def _instantiate_meeting_item(self):
        """
        Instantiate the item from the raw and parsed item we have
        """


        # FIXME: these need to return some values
        MeetingItem._get_council = MagicMock(return_value={'id': u'1', 'name': u'Den Helder'})
        MeetingItem._get_committees = MagicMock(return_value={})

        item = MeetingItem(
            self.source_definition, 'application/json',
            self.raw_item, self.meeting_item
        )
        return item


    def test_meeting_get_original_object_id(self):
        item = self._instantiate_meeting()
        self.assertEqual(item.get_original_object_id(), self.meeting_object_id)


    def test_meeting_item_get_original_object_id(self):
        item = self._instantiate_meeting_item()
        self.assertEqual(
            item.get_original_object_id(), self.meeting_item_object_id)


    def test_meeting_get_original_object_urls(self):
        item = self._instantiate_meeting()
        self.assertDictEqual(
            item.get_original_object_urls(), self.meeting_object_urls)


    def test_meeting_item_get_original_object_urls(self):
        item = self._instantiate_meeting_item()
        self.assertDictEqual(
            item.get_original_object_urls(), self.meeting_item_object_urls)


    def test_meeting_get_rights(self):
        item = self._instantiate_meeting()
        self.assertEqual(item.get_rights(), self.rights)


    def test_meeting_item_get_rights(self):
        item = self._instantiate_meeting_item()
        self.assertEqual(item.get_rights(), self.rights)


    def test_meeting_get_collection(self):
        item = self._instantiate_meeting()
        self.assertEqual(item.get_collection(), self.collection)


    def test_meeting_item_get_collection(self):
        item = self._instantiate_meeting_item()
        self.assertEqual(item.get_collection(), self.collection)

    def test_meeting_name(self):
        item = self._instantiate_meeting()
        data = item.get_combined_index_data()
        self.assertEqual(data['name'], self.meeting_name)


    def test_meeting_item_name(self):
        item = self._instantiate_meeting_item()
        data = item.get_combined_index_data()
        self.assertEqual(data['name'], self.meeting_item_name)

    def test_meeting_identifiers(self):
        item = self._instantiate_meeting()
        data = item.get_combined_index_data()
        self.assertEqual(data['identifiers'], self.meeting_identifiers)


    def test_meeting_item_identifiers(self):
        item = self._instantiate_meeting_item()
        data = item.get_combined_index_data()
        self.assertEqual(data['identifiers'], self.meeting_item_identifiers)

    def test_meeting_organisation(self):
        item = self._instantiate_meeting()
        data = item.get_combined_index_data()
        self.assertDictEqual(data['organisation'], self.organisation)


    def test_meeting_item_organisation(self):
        item = self._instantiate_meeting_item()
        data = item.get_combined_index_data()
        self.assertDictEqual(data['organisation'], self.organisation)


    def test_meeting_classification(self):
        item = self._instantiate_meeting()
        data = item.get_combined_index_data()
        self.assertEqual(data['classification'], self.meeting_classification)


    def test_meeting_item_classification(self):
        item = self._instantiate_meeting_item()
        data = item.get_combined_index_data()
        self.assertEqual(data['classification'], self.meeting_item_classification)

    def test_meeting_dates(self):
        item = self._instantiate_meeting()
        data = item.get_combined_index_data()
        self.assertEqual(data['start_date'], self.start_date)
        self.assertEqual(data['end_date'], self.start_date)


    def test_meeting_item_dates(self):
        item = self._instantiate_meeting_item()
        data = item.get_combined_index_data()
        self.assertEqual(data['start_date'], self.start_date)
        self.assertEqual(data['end_date'], self.start_date)


    def test_meeting_location(self):
        item = self._instantiate_meeting()
        data = item.get_combined_index_data()
        self.assertEqual(data['location'], self.location)


    def test_meeting_item_location(self):
        item = self._instantiate_meeting_item()
        data = item.get_combined_index_data()
        self.assertEqual(data['location'], self.location)


    def test_meeting_status(self):
        item = self._instantiate_meeting()
        data = item.get_combined_index_data()
        self.assertEqual(data['status'], self.status)


    def test_meeting_item_status(self):
        item = self._instantiate_meeting_item()
        data = item.get_combined_index_data()
        self.assertEqual(data['status'], self.status)


    def test_get_object_id_for(self):
        item = self._instantiate_meeting()
        self.assertEqual(item._get_object_id_for(
            item.get_original_object_id(),
            item.get_original_object_urls()
        ), item.get_object_id())


    def test_meeting_item_get_parent_id(self):
        meeting = self._instantiate_meeting()
        item = self._instantiate_meeting_item()
        data = item.get_combined_index_data()
        self.assertEqual(data['parent_id'], meeting.get_object_id())


    def test_meeting_sources(self):
        item = self._instantiate_meeting()
        data = item.get_combined_index_data()
        self.assertEqual(data['sources'], self.meeting_sources)


    def test_meeting_item_sources(self):
        item = self._instantiate_meeting_item()
        data = item.get_combined_index_data()
        self.assertEqual(data['sources'], self.meeting_item_sources)


    def test_meeting_description(self):
        item = self._instantiate_meeting()
        data = item.get_combined_index_data()
        self.assertEqual(data['description'], self.meeting_description)


    def test_meeting_item_description(self):
        item = self._instantiate_meeting_item()
        data = item.get_combined_index_data()
        self.assertEqual(data['description'], self.meeting_item_description)

    def test_faulty_meeting_item(self):
        # # FIXME: these need to return some values
        MeetingItem._get_council = MagicMock(return_value={'id': u'1', 'name': u'Den Helder'})
        MeetingItem._get_committees = MagicMock(return_value={})
        # MeetingItem._get_documents_html_for_item = MagicMock(return_value=self.docs_raw_item)

        meeting_item = {
            'type': 'meeting-item',
            'content': self.raw_faulty_meeting_item,
            'full_content': self.raw_faulty_item
        }

        item = MeetingItem(
            self.source_definition, 'application/json',
            self.raw_faulty_meeting_item, meeting_item
        )

        #data = item.get_combined_index_data()
        meeting_item_id = item._get_meeting_item_id()
        self.assertEqual(meeting_item_id, self.faulty_meeting_item_id)

        meeting_item_documents_url = item._get_meeting_item_documents_url()
        self.assertEqual(meeting_item_documents_url, self.faulty_meeting_item_documents_url)
