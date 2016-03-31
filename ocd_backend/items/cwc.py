from datetime import datetime
import json
from pprint import pprint
from hashlib import sha1
from time import sleep
import re

import iso8601

from ocd_backend.items.popolo import EventItem
from ocd_backend.utils.misc import slugify
from ocd_backend import settings
from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.utils.api import FrontendAPIMixin
from ocd_backend.utils.pdf import PDFToTextMixin


class VideotulenItem(
        EventItem, HttpRequestMixin, FrontendAPIMixin, PDFToTextMixin):
    def _get_council(self):
        """
        Gets the organisation that represents the council.
        """

        results = self.api_request(
            self.source_definition['index_name'], 'organizations',
            classification='Council')
        return results[0]

    def _get_committees(self):
        """
        Gets the committees that are active for the council.
        """

        results = self.api_request(
            self.source_definition['index_name'], 'organizations',
            classification=['committee', 'subcommittee'])
        return {unicode(c['name']): c for c in results}

    def get_original_object_id(self):
        return unicode(self.original_item['Webcast']['Id']).strip()

    def get_original_object_urls(self):
        return {"html": unicode(self.original_item['Webcast']['RegisterUrl']).strip()}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_combined_index_data(self):
        combined_index_data = {}
        council = self._get_council()
        committees = self._get_committees()

        combined_index_data['id'] = unicode(self.get_object_id())

        combined_index_data['hidden'] = self.source_definition['hidden']

        if self.original_item['Webcast'].has_key('Title'):
            combined_index_data['name'] = u'%s' % (
                unicode(self.original_item['Webcast']['Title']),)
        else:
            combined_index_data['name'] = self.get_collection()

        combined_index_data['identifiers'] = [
            {
                'identifier': unicode(self.original_item['Webcast']['Id']),
                'scheme': u'CWC'
            },
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            }
        ]

        try:
            combined_index_data['organization_id'] = committees[
                combined_index_data['name']]['id']
            combined_index_data['organization'] = committees[
                combined_index_data['name']]
        except KeyError as e:
            combined_index_data['organization_id'] = council['id']
            combined_index_data['organization'] = council

        combined_index_data['classification'] = u'Videotulen %s' % (
            combined_index_data['name'],)

        topic_descriptions = []
        for topic in self.original_item['Webcast']['Topics']['Topic']:
            topic_description = topic.get('Description')
            if topic_description is None:
                topic_description = u''
            topic_descriptions.append(
                u'<h3>%s</h3>\n<p>%s</p>' % (topic['Title'], topic_description,))

        if len(topic_descriptions) > 0:
            combined_index_data['description'] = u'\n'.join(topic_descriptions)
        else:
            combined_index_data['description'] = self.original_item['Webcast']['Description']


        if self.original_item['Webcast'].has_key('ActualStart'):
            start_date_field = 'ActualStart'
            end_date_field = 'ActualEnd'
        else:
            start_date_field = 'ScheduledStart'
            end_date_field = 'ScheduledStart'

        combined_index_data['start_date'] = iso8601.parse_date(
            self.original_item['Webcast'][start_date_field],)
        combined_index_data['end_date'] = iso8601.parse_date(
            self.original_item['Webcast'][end_date_field],)
        combined_index_data['location'] = u'Raadszaal'
        combined_index_data['status'] = u'confirmed'

        # if self.original_item.has_key('MeetingItems'):
        #     combined_index_data['children'] = [
        #         self._get_meeting_id(mi) for mi in self.original_item[
        #             'MeetingItems']]

        combined_index_data['sources'] = []

        # try:
        #     documents = self.original_item['Documents']
        # except KeyError as e:
        #     documents = []
        # if documents is None:
        #     documents = []
        #
        # for document in documents:
        #     sleep(1)
        #     print u"%s: %s" % (
        #         combined_index_data['name'], document['DisplayName'],)
        #     description = self.pdf_get_contents(
        #         document['PublicDownloadURL'],
        #         self.source_definition.get('pdf_max_pages', 20))
        #     combined_index_data['sources'].append({
        #         'url': document['PublicDownloadURL'],
        #         'note': document['DisplayName'],
        #         'description': description
        #     })

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
