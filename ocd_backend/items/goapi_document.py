from hashlib import sha1
import iso8601

from ocd_backend.items.popolo import EventItem
from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.utils.api import FrontendAPIMixin
from ocd_backend.utils.file_parsing import FileToTextMixin


class Document(
        EventItem, HttpRequestMixin, FrontendAPIMixin, FileToTextMixin):

    def _get_current_permalink(self):
        return u'%s/v2/documents/%i' % (self.source_definition[
                                    'base_url'], self.original_item['id'])

    @staticmethod
    def get_document_id(document):
        hash_content = u'document-%s' % (document['id'])
        return unicode(sha1(hash_content.decode('utf8')).hexdigest())

    def get_object_id(self):
        return self.get_document_id(self.original_item)

    def get_original_object_id(self):
        return unicode(self.original_item['id']).strip()

    def get_original_object_urls(self):
        return {"html": self._get_current_permalink()}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_combined_index_data(self):
        combined_index_data = {}

        current_permalink = self._get_current_permalink()

        combined_index_data['id'] = unicode(self.get_object_id())

        combined_index_data['hidden'] = self.source_definition['hidden']

        if self.original_item['description']:
            combined_index_data['name'] = unicode(
                self.original_item['description'])
        else:
            combined_index_data['name'] = unicode(
                self.original_item['fileName'])
        combined_index_data['classification'] = unicode(
            self.original_item['documentTypeLabel'])

        combined_index_data['identifiers'] = [
            {
                'identifier': unicode(self.original_item['id']),
                'scheme': u'GemeenteOplossingen'
            },
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            }
        ]

        # TODO: include timezone in response
        combined_index_data['start_date'] = iso8601.parse_date(
            self.original_item['publicationDate']['date'].replace(' ', 'T'))

        combined_index_data['sources'] = []

        url = u"%s/download" % (current_permalink,)
        description = self.file_get_contents(
            url,
            self.source_definition.get('pdf_max_pages', 20)
        )

        combined_index_data['sources'].append({
            'url': url,
            'note': self.original_item['fileName'],
            'description': description
        })

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
