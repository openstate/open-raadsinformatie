from hashlib import sha1
import iso8601

from ocd_backend.items.notubiz_meeting import Meeting


def get_meetingitem_id(item_id):
    hash_content = u'meetingitem-%s' % item_id
    return unicode(sha1(hash_content.decode('utf8')).hexdigest())


class MeetingItem(Meeting):

    @staticmethod
    def _get_meeting_id(item_id):
        from ocd_backend.items.notubiz_meeting import get_meeting_id
        return get_meeting_id(item_id)

    def get_object_id(self):
        return get_meetingitem_id(self.original_item['id'])

    def _get_current_permalink(self):
        return u'%s/agenda_items/agenda_points/%i' % (self.source_definition['base_url'], self.original_item['id'])

    def get_combined_index_data(self):
        combined_index_data = dict()

        combined_index_data['id'] = unicode(self.get_object_id())
        combined_index_data['hidden'] = self.source_definition['hidden']

        meeting = self.original_item.get('meeting')

        try:
            combined_index_data['name'] = self.original_item['attributes']['1']
        except KeyError:
            combined_index_data['name'] = self.original_item['type_data']['title']

        combined_index_data['classification'] = u'Agendapunt'

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

        try:
            combined_index_data['parent_id'] = get_meetingitem_id(self.original_item['parent']['id'])
        except TypeError:
            combined_index_data['parent_id'] = self._get_meeting_id(self.original_item['meeting']['id'])

        #combined_index_data['location'] = self.original_item['attributes']['50']

        if meeting['plannings'][0]['start_date']:
            combined_index_data['start_date'] = iso8601.parse_date(
                meeting['plannings'][0]['start_date']
            )
            combined_index_data['date_granularity'] = 8

        if meeting['plannings'][0]['end_date']:
            combined_index_data['end_date'] = iso8601.parse_date(
                meeting['plannings'][0]['end_date']
            )
            combined_index_data['date_granularity'] = 8

        if 'agenda_items' in self.original_item:
            combined_index_data['children'] = [
                get_meetingitem_id(item['id']) for item in self.original_item['agenda_items']
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