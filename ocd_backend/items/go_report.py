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

    def _get_meeting_items(self):
        items = []
        for meeting_item_html in self.full_html.xpath(
            '//li[contains(@class, "agendaRow")]'):
                meeting_item_obj = {
                    'index': int(u''.join(meeting_item_html.xpath('.//div[@class="first"]//text()'))),
                    'title': u''.join(meeting_item_html.xpath('.//div[@class="title"]/h3//text()')),
                    'description': u''.join(meeting_item_html.xpath('.//div[@class="toelichting"]//text()')),
                }
                items.append(meeting_item_obj)
        return items


    def get_original_object_id(self):
        return u'%s#downloaden' % (self._get_stable_permalink(),)

    def get_original_object_urls(self):
        return {
            "html": u'%s#downloaden' % (self._get_current_permalink(),),
            "mp3": self._get_mp3_link()
        }

    def get_collection(self):
        return u'Verslag %s' % (super(ReportItem, self).get_collection(),)

    def get_combined_index_data(self):
        combined_index_data = super(ReportItem, self).get_combined_index_data()

        combined_index_data['name'] = u'Verslag %s' % (combined_index_data['name'],)

        combined_index_data['classification'] = u'Report'

        # TODO: get all the descriptive content?
        items = self._get_meeting_items()
        combined_index_data['description'] = u'\n'.join(
            [u"%s. %s\n\n%s" % (i['index'], i['title'], i['description'],) for i in items])

        for identifier in combined_index_data['identifiers']:
            if identifier['scheme'] == u'GemeenteOplossingen':
                identifier['identifier'] += '#downloaden'

        return combined_index_data
