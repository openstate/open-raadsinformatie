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
            html.xpath('//div[@id="content"]/h2//text()')).strip()

        combined_index_data['identifiers'] = [
            {
                'identifier': combined_index_data['id'],
                'scheme': u'ORI'
            },
            {
                'identifier': u''.join(html.xpath(
                    '//meta[@name="DCTERMS.identifier"]/@content')).replace(
                        u'.html', u''),
                'scheme': u'Almanak'
            }

        ]
        combined_index_data['email'] = u''.join(html.xpath(
            '//a[starts-with(@href,"mailto:")]/text()'))
        # TODO: should explicitly check for female prefixes
        combined_index_data['gender'] = (
            u'male' if combined_index_data['name'].startswith(u'Dhr. ') else
            u'female')

        parties = self.original_item['parties']
        party = u''.join(
            html.xpath('//ul[@class="definitie"]/li/ul/li')[0].xpath(
                './/text()'))
        party_id = parties[party]['id'] if parties.has_key(party) else None
        party_obj = parties[party] if parties.has_key(party) else None
        role = u''.join(
            html.xpath('//div[@id="content"]//h3/text()')).strip()
        try:
            council_obj = [
                p for p in parties.values() if (
                    p['classification'] == u'Council')][0]
            council_id = council_obj['id']
        except IndexError as e:
            council_obj = None
            council_id = None

        combined_index_data['memberships'] = [
            {
                'label': role,
                'role': role,
                'person_id': combined_index_data['id'],
                'organization_id': council_id,
                'organization': council_obj
            }
        ]
        if party_id is not None:
            combined_index_data['memberships'].append({
                'label': role,
                'role': role,
                'person_id': combined_index_data['id'],
                'organization_id': party_id,
                'organization': party_obj
            })

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
