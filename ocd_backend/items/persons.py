from datetime import datetime

from lxml import etree
import requests

from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.items.popolo import PersonItem


class AlmanakPersonItem(HttpRequestMixin, PersonItem):
    def get_original_object_id(self):
        return u'https://almanak.overheid.nl%s' % (
            unicode(self.original_item['url']),)

    def get_original_object_urls(self):
        return {"html": self.get_original_object_id()}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return self.original_item['municipality']

    def get_combined_index_data(self):
        combined_index_data = {}

        request_url = u'https://almanak.overheid.nl%s' % (
            unicode(self.original_item['url']),)

        r = self.http_session.get(request_url, verify=False)
        r.raise_for_status()
        html = etree.HTML(r.content)

        combined_index_data['id'] = unicode(self.get_object_id())

        combined_index_data['hidden'] = self.source_definition['hidden']

        combined_index_data['name'] = u''.join(
            html.xpath('//div[id=\"content\"]/h2/text()')).strip()

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
