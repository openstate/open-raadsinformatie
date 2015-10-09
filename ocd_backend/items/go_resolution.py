import urlparse

from .go_meeting import MeetingItem

class ResolutionItem(MeetingItem):
    def _get_resolution_document(self):

        for item in self.full_html.xpath('//div[@id="documenten"]//li/a[1]'):
            anchor = u''.join(item.xpath('./@href'))
            if u'Besluitenlijst' in anchor:
                return anchor

    def _get_pdf_link(self):
        og_url = u''.join(
            self.full_html.xpath('//meta[@property="og:url"]/@content')).strip()
        return urlparse.urljoin(og_url, self._get_resolution_document())

    def get_original_object_id(self):
        return u'%s#documenten' % (self._get_stable_permalink(),)

    def get_original_object_urls(self):
        return {
            "html": u'%s#documenten' % (self._get_current_permalink(),),
            "pdf": self._get_pdf_link()
        }

    def get_collection(self):
        return u'Besluitenlijst %s' % (super(ResolutionItem, self).get_collection(),)

    def get_combined_index_data(self):
        combined_index_data = super(ResolutionItem, self).get_combined_index_data()

        combined_index_data['name'] = u'Besluitenlijst %s' % (combined_index_data['name'],)

        combined_index_data['classification'] = u'Resolution'

        combined_index_data['description'] = self.pdf_get_contents(
            self.get_original_object_urls()['pdf'],
            self.source_definition.get('pdf_max_pages', 20))

        for identifier in combined_index_data['identifiers']:
            if identifier['scheme'] == u'GemeenteOplossingen':
                identifier['identifier'] += '#documenten'

        return combined_index_data
