import urlparse

from .go_meeting import MeetingItem

class ReportItem(MeetingItem):
    def _get_report_document(self):

        for item in self.full_html.xpath('//div[@id="downloaden"]//li/a[1]'):
            anchor = u''.join(item.xpath('./@href'))
            if u'mp3' in anchor:
                return anchor

    def _get_mp3_link(self):
        og_url = u''.join(
            self.full_html.xpath('//meta[@property="og:url"]/@content')).strip()
        return urlparse.urljoin(og_url, self._get_report_document())

    def get_original_object_id(self):
        og_url = u''.join(
            self.full_html.xpath('//meta[@property="og:url"]/@content')).strip()
        return u'%s#downloaden' % (og_url,)

    def get_original_object_urls(self):
        return {
            "html": self.get_original_object_id(),
            "mp3": self._get_mp3_link()
        }

    def get_collection(self):
        return u'Verslag %s' % (super(ReportItem, self).get_collection(),)

    def get_combined_index_data(self):
        combined_index_data = super(ReportItem, self).get_combined_index_data()

        combined_index_data['name'] = u'Verslag %s' % (combined_index_data['name'],)

        combined_index_data['classification'] = u'Report'

        # TODO: get all the descriptive content?
        combined_index_data['description'] = u''

        return combined_index_data
