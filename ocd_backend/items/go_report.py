import urlparse

from .go_meeting import MeetingItem


class ReportItem(MeetingItem):
    def _get_report_document(self):
        for item in self.full_html.xpath('//div[@id="downloaden"]//li/a[1]'):
            anchor = u''.join(item.xpath('./@href')).strip()
            if u'mp3' in anchor:
                return anchor

    def _get_mp3_link(self):
        anchor = self._get_report_document()
        if anchor is not None:
            og_url = u''.join(
                self.full_html.xpath('//meta[@property="og:url"]/@content')).strip()
            return urlparse.urljoin(og_url, anchor)

    def _get_meeting_items(self):
        items = []
        for meeting_item_html in self.full_html.xpath(
                '//li[contains(@class, "agendaRow")]'):
            meeting_item_obj = {
                'index': u''.join(meeting_item_html.xpath('.//div[@class="first"]//text()')).strip(),
                'title': u''.join(meeting_item_html.xpath('.//div[@class="title"]/h3//text()')),
                'description': u''.join(meeting_item_html.xpath('.//div[@class="toelichting"]//text()')),
            }
            items.append(meeting_item_obj)
        return items

    def get_original_object_id(self):
        return u'%s#downloaden' % (self._get_stable_permalink(),)

    def get_original_object_urls(self):
        urls = {
            "html": u'%s#downloaden' % (self._get_current_permalink(),)
        }
        mp3_link = self._get_mp3_link()
        if mp3_link is not None:
            urls['mp3'] = mp3_link
        return urls

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        object_model = super(ReportItem, self).get_object_model()

        object_model['name'] = u'Verslag %s' % (object_model['name'],)

        object_model['classification'] = u'Verslag'

        # TODO: get all the descriptive content?
        items = self._get_meeting_items()
        object_model['description'] = u'\n'.join(
            [u"%s. %s\n\n%s" % (i['index'], i['title'], i['description'],) for i in items])

        for identifier in object_model['identifiers']:
            if identifier['scheme'] == u'GemeenteOplossingen':
                identifier['identifier'] += '#downloaden'

        return object_model
