from lxml import etree

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
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        object_model = {}

        request_url = u'https://almanak.overheid.nl%s' % (
            unicode(self.original_item['url']),)

        r = self.http_session.get(request_url, verify=False)
        r.raise_for_status()
        html = etree.HTML(r.content)

        object_model['id'] = unicode(self.get_object_id())

        object_model['hidden'] = self.source_definition['hidden']

        object_model['name'] = u''.join(
            html.xpath('//div[@id="content"]/h2//text()')).strip()

        object_model['identifiers'] = [
            {
                'identifier': object_model['id'],
                'scheme': u'ORI'
            },
            {
                'identifier': u''.join(html.xpath(
                    '//meta[@name="DCTERMS.identifier"]/@content')).replace(
                        u'.html', u''),
                'scheme': u'Almanak'
            }

        ]
        object_model['email'] = u''.join(html.xpath(
            '//a[starts-with(@href,"mailto:")]/text()'))
        # TODO: should explicitly check for female prefixes
        object_model['gender'] = (
            u'male' if object_model['name'].startswith(u'Dhr. ') else
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

        object_model['memberships'] = [
            {
                'label': role,
                'role': role,
                'person_id': object_model['id'],
                'organization_id': council_id,
                'organization': council_obj
            }
        ]
        if party_id is not None:
            object_model['memberships'].append({
                'label': role,
                'role': role,
                'person_id': object_model['id'],
                'organization_id': party_id,
                'organization': party_obj
            })

        return object_model

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
