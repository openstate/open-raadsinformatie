from datetime import datetime
import json
from pprint import pprint
from hashlib import sha1

import iso8601

from ocd_backend.items.popolo import EventItem
from ocd_backend.utils.misc import slugify
from ocd_backend import settings
from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.utils.api import FrontendAPIMixin


class IBabsMeetingItem(EventItem, HttpRequestMixin, FrontendAPIMixin):
    def _get_council(self):
        """
        Gets the organisation that represents the council.
        """

        results = self.api_request(
            self.source_definition['index_name'], 'organisations',
            classification='council')
        return results[0]

    def _find_meeting_type_id(self, org):
        results = [x for x in org['identifiers'] if x['scheme'] == u'iBabs']
        return results[0]['identifier']

    def _get_committees(self):
        """
        Gets the committees that are active for the council.
        """

        results = self.api_request(
            self.source_definition['index_name'], 'organisations',
            classification=['committee', 'subcommittee'])
        return {self._find_meeting_type_id(c): c['id'] for c in results}

    def _get_meeting_id(self, meeting):
        hash_content = u'meeting-%s' % (meeting['Id'])
        return sha1(hash_content.decode('utf8')).hexdigest()

    def get_object_id(self):
        return self._get_meeting_id(self.original_item)

    def get_original_object_id(self):
        return unicode(self.original_item['Id']).strip()

    def get_original_object_urls(self):
        # FIXME: what to do when there is not an original URL?
        return {"html": settings.IBABS_WSDL}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        meeting = self.original_item
        if self.original_item.has_key('MeetingId'):
            meeting = self.original_item['Meeting']
        return u'%s' % (meeting['Meetingtype'],)

    def get_combined_index_data(self):
        combined_index_data = {}
        council = self._get_council()
        committees = self._get_committees()

        meeting = self.original_item
        if self.original_item.has_key('MeetingId'):
            meeting = self.original_item['Meeting']

        combined_index_data['id'] = unicode(self.get_object_id())

        combined_index_data['hidden'] = self.source_definition['hidden']

        if self.original_item.has_key('Title'):
            combined_index_data['name'] = unicode(self.original_item['Title'])
        else:
            combined_index_data['name'] = self.get_collection()

        combined_index_data['identifiers'] = [
            {
                'identifier': unicode(self.original_item['Id']),
                'scheme': u'iBabs'
            },
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            }
        ]

        try:
            combined_index_data['organisation_id'] = committees[
                meeting['MeetingtypeId']]
        except KeyError as e:
            combined_index_data['organisation_id'] = council['id']

        combined_index_data['classification'] = (
            u'Meeting Item' if self.original_item.has_key('MeetingId') else
            u'Meeting')
        combined_index_data['description'] = self.original_item['Explanation']
        combined_index_data['start_date'] = iso8601.parse_date(
            meeting['MeetingDate'],)
        combined_index_data['end_date'] = iso8601.parse_date(
            meeting['MeetingDate'],)
        combined_index_data['location'] = meeting['Location'].strip()
        combined_index_data['status'] = u'confirmed'

        if self.original_item.has_key('MeetingId'):
            combined_index_data['parent_id'] = unicode(self._get_meeting_id(
                meeting))

        # TODO: documents

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
