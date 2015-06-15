from datetime import datetime
import json
from pprint import pprint

import iso8601

from ocd_backend.items.popolo import EventItem
from ocd_backend.utils.misc import slugify
from ocd_backend import settings
from ocd_backend.extractors import HttpRequestMixin


class IBabsMeetingItem(EventItem, HttpRequestMixin):
    def _get_council(self):
        """
        Gets the organisation that represents the council.
        """

        # TODO: not currently likely that we will have more than 100 orgs.
        organisations_url = u'%s%s/organisations/search' % (
            settings.API_URL, self.source_definition['index_name'],)

        # TODO: filter on end date of council organisation
        organisation_query = {
            "query": self.source_definition['sitename'],
            "filters": {
                "classification": {"terms": ["council"]}
            },
            "size": 1
        }
        pprint(organisation_query)
        r = self.http_session.post(
            organisations_url,
            data=json.dumps(organisation_query)
        )
        r.raise_for_status()
        pprint(r.json())
        return r.json()['organisations'][0]

    def get_original_object_id(self):
        return unicode(self.original_item['Id']).strip()

    def get_original_object_urls(self):
        # FIXME: what to do when there is not an original URL?
        return {"html": settings.IBABS_WSDL}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        # FIXME: should be based on meeting type descriptions ...
        meeting = self.original_item
        if self.original_item.has_key('MeetingId'):
            meeting = self.original_item['Meeting']
        return u'%s %s' % (meeting['Meetingtype'], meeting['MeetingDate'],)

    def get_combined_index_data(self):
        combined_index_data = {}
        council = self._get_council()

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

        # TODO: should add organisations for commissions
        combined_index_data['organisation_id'] = council['id']

        combined_index_data['classification'] = (
            u'Meeting Item' if self.original_item.has_key('MeetingId') else
            u'Meeting')
        combined_index_data['description'] = self.original_item['Explanation']
        combined_index_data['start_date'] = iso8601.parse_date(
            meeting['MeetingDate'],)
        combined_index_data['end_date'] = iso8601.parse_date(
            meeting['MeetingDate'],)
        combined_index_data['location'] = meeting['Location']
        combined_index_data['status'] = u'confirmed'
        # TODO: Get the organization id somehow.. needs stable meeting ids
        if self.original_item.has_key('MeetingId'):
            combined_index_data['parent_id'] = self.original_item['MeetingId']

        # TODO: documents

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
