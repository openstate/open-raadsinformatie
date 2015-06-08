import json
from pprint import pprint

from lxml import etree

from ocd_frontend import settings

from .staticfile import StaticHtmlExtractor


class OrganisationsExtractor(StaticHtmlExtractor):
    """
    Extract items from an OData Feed.
    """

    def extract_items(self, static_content):
        """
        Extracts items from a JSON file. It is assumed to be an array
        of items.
        """

        organisations = {}
        html = etree.HTML(static_content)

        try:
            council = {
                'name': html.xpath('//h2/text()')[0],
                'cassification': u'Council'}
        except IndexError as e:
            council = {}
        organisations[council['name']] = council

        for link in html.xpath('//ul[@class="definitie"][2]//ul//li//a'):
            line = u''.join(link.xpath('.//text()'))
            person, party = [l.strip() for l in line.split(u'\xa0', 1)]
            organisations[party[1:-1]] = (
                {'name': party[1:-1], 'classification': u'Party'})

        pprint(organisations)

        for item in organisations.values():
            yield 'application/json', json.dumps(item)


class PersonsExtractor(StaticHtmlExtractor):
    """
    Extract persons from an Almanak
    """

    def _get_parties(self):
        """
        Gets a list of parties from the frontend API in JSON format.
        """
        # TODO: not currently likely that we will have more than 100 orgs.
        organisations_url = u'%s%s/organisations/search?size=100' % (
            settings.API_URL, self.source_definition['index_name'],)
        r = self.http_session.get(organisations_url, verify=False)
        r.raise_for_status()
        return r.json()

    def extract_items(self, static_content):
        """
        Extracts persons from a HTML file. Also passes parties to the item
        transformer.
        """

        html = etree.HTML(static_content)
        parties = self._get_parties()
        municipality = u''.join(html.xpath('//h2/text()')).strip()

        for person in html.xpath('//ul[@class="definitie"][2]//ul//li//a'):
            person_url = (u''.join(person.xpath('.//@href'))).strip()
            person_text = (u''.join(person.xpath('.//text()'))).strip()

            if person_url != '':
                # TODO: fields are not the best, but hey :)
                yield 'application/json', json.dumps({
                    'url': person_url,
                    'parties': parties,
                    'text': person_text,
                    'municipality': municipality
                })
