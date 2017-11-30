from hashlib import sha1
import iso8601

from ocd_backend.items.popolo import EventItem
from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.utils.api import FrontendAPIMixin
from ocd_backend.utils.file_parsing import FileToTextMixin


def get_meeting_id(item_id):
    hash_content = u'meeting-%s' % item_id
    return unicode(sha1(hash_content.decode('utf8')).hexdigest())


class Meeting(EventItem, HttpRequestMixin, FrontendAPIMixin, FileToTextMixin):

    @staticmethod
    def _get_meetingitem_id(item_id):
        from ocd_backend.items.notubiz_meetingitem import get_meetingitem_id
        return get_meetingitem_id(item_id)

    def _get_current_permalink(self):
        return u'%s/events/meetings/%i' % (self.source_definition['base_url'], self.original_item['id'])

    def get_object_id(self):
        return get_meeting_id(self.original_item['id'])

    def get_original_object_id(self):
        return unicode(self.original_item['id']).strip()

    def get_original_object_urls(self):
        return {"html": self._get_current_permalink()}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_combined_index_data(self):
        combined_index_data = dict()

        combined_index_data['id'] = unicode(self.get_object_id())

        combined_index_data['hidden'] = self.source_definition['hidden']

        if self.original_item['plannings'][0]['start_date']:
            combined_index_data['start_date'] = iso8601.parse_date(
                self.original_item['plannings'][0]['start_date']
            )

        if self.original_item['plannings'][0]['end_date']:
            combined_index_data['end_date'] = iso8601.parse_date(
                self.original_item['plannings'][0]['end_date']
            )

        combined_index_data['name'] = 'Vergadering %s %s' % (self.original_item['attributes']['1'], combined_index_data['start_date'])
        combined_index_data['description'] = self.original_item['attributes']['3']
        combined_index_data['classification'] = u'Agenda'

        combined_index_data['identifiers'] = [
            {
                'identifier': unicode(self.original_item['id']),
                'scheme': u'Notubiz'
            },
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            }
        ]

        combined_index_data['organization_id'] = unicode(self.original_item['organisation']['id'])
        #combined_index_data['organization'] = self.original_item['body']


        # combined_index_data['last_modified'] = iso8601.parse_date(
        #    self.original_item['last_modified'])

        combined_index_data['location'] = self.original_item['attributes']['50']

        if self.original_item['canceled']:
            combined_index_data['status'] = u'cancelled'
        elif self.original_item['inactive']:
            combined_index_data['status'] = u'inactive'
        else:
            combined_index_data['status'] = u'confirmed'

        if 'agenda_items' in self.original_item:
            combined_index_data['children'] = [
                self._get_meetingitem_id(item['id']) for item in self.original_item['agenda_items']
            ]

        combined_index_data['sources'] = [
            {
                'url': self._get_current_permalink(),
                'note': u''
            }
        ]

        media_urls = []
        for doc in self.original_item.get('documents', []):
            media_urls.append(
                {
                    "url": "/v0/resolve/",
                    "note": doc['title'],
                    "original_url": doc['url']
                }
            )
        if media_urls:
            combined_index_data['media_urls'] = media_urls

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
