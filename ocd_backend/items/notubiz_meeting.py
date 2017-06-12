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
        return u'%s%i' % (self.source_definition['base_url'], self.original_item['id'])

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

        combined_index_data['name'] = self.original_item['name']
        combined_index_data['description'] = self.original_item['description']
        combined_index_data['classification'] = u'Agenda'

        combined_index_data['identifiers'] = [
            {
                'identifier': unicode(self.original_item['notubiz_id']),
                'scheme': u'Notubiz'
            },
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            }
        ]

        combined_index_data['organization'] = {'name': self.original_item['jurisdiction']}

        combined_index_data['start_date'] = iso8601.parse_date(
            self.original_item['start_time'])
        # combined_index_data['last_modified'] = iso8601.parse_date(
        #    self.original_item['last_modified'])

        combined_index_data['location'] = self.original_item['location']
        combined_index_data['status'] = u'confirmed'

        if 'agenda' in self.original_item:
            combined_index_data['children'] = [self._get_meetingitem_id(mi['id']) for mi in self.original_item['agenda']]

        combined_index_data['sources'] = [
            {
                'url': self._get_current_permalink(),
                'note': u''
            }
        ]

        try:
            documents = self.original_item['documents']
        except KeyError:
            documents = []

        if documents is None:
            documents = []

        for document in documents:
            # sleep(1)
            description = self.file_get_contents(
                document['url'],
                self.source_definition.get('pdf_max_pages', 20),
                self.final_try
            )

            if description:
                source = {
                    'url': document['url'],
                    'note': document['text'],
                    'description': description
                }
            else:
                source = {
                    'url': document['url'],
                    'note': u'Unable to download or parse this file'
                }

            combined_index_data['sources'].append(source)

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
