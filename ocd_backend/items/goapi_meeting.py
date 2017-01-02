from hashlib import sha1
import iso8601

from ocd_backend.items.popolo import EventItem
from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.utils.api import FrontendAPIMixin
from ocd_backend.utils.pdf import PDFToTextMixin


class Meeting(
        EventItem, HttpRequestMixin, FrontendAPIMixin, PDFToTextMixin):

    def _get_current_permalink(self):
        return u'%s/meetings/%i' % (self.source_definition[
                                    'base_url'], self.original_item['id'])

    def _find_meeting_type_id(self, org):
        results = [x for x in org['identifiers']
                   if x['scheme'] == u'GemeenteOplossingen']
        return results[0]['identifier']

    def _get_committees(self):
        """
        Gets the committees that are active for the council.
        """

        results = self.api_request(
            self.source_definition['index_name'], 'organizations',
            classification=['committee', 'subcommittee'])
        return {self._find_meeting_type_id(c): c for c in results}

    @staticmethod
    def get_meeting_id(meeting):
        hash_content = u'meeting-%s' % (meeting['id'])
        return unicode(sha1(hash_content.decode('utf8')).hexdigest())

    def get_object_id(self):
        return self.get_meeting_id(self.original_item)

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

        committees = self._get_committees()
        current_permalink = self._get_current_permalink()

        combined_index_data['id'] = unicode(self.get_object_id())

        combined_index_data['hidden'] = self.source_definition['hidden']

        combined_index_data['name'] = self.original_item['description']
        combined_index_data['classification'] = u'Agenda'

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

        try:
            combined_index_data['organization'] = committees[
                self.original_item['dmu']['id']]
        except KeyError:
            pass

        combined_index_data['organization_id'] = unicode(
            self.original_item['dmu']['id'])

        combined_index_data['start_date'] = iso8601.parse_date(
            self.original_item['date'])

        combined_index_data['location'] = self.original_item['location']
        combined_index_data['status'] = u'confirmed'
        combined_index_data['sources'] = [
            {
                'url': current_permalink,
                'note': u''
            }
        ]

        if 'items' in self.original_item:
            combined_index_data['children'] = [
                self.get_meeting_id(mi) for mi in self.original_item['items']]

        combined_index_data['sources'] = []

        try:
            documents = self.original_item['documents']
        except KeyError:
            documents = []

        if documents is None:
            documents = []

        for document in documents:
            # sleep(1)
            url = u"%s/documents/%s" % (current_permalink, document['id'])
            description = self.pdf_get_contents(
                url,
                self.source_definition.get('pdf_max_pages', 20)
            )

            combined_index_data['sources'].append({
                'url': url,
                'note': document['filename'],
                'description': description
            })

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
