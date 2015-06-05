import json

from lxml import etree

from .staticfile import StaticJSONExtractor


class OrganisationsExtractor(StaticJSONExtractor):
    """
    Extract items from an OData Feed.
    """

    def extract_items(self, static_content):
        """
        Extracts items from a JSON file. It is assumed to be an array
        of items.
        """

        organisations = []
        html = etree.HTML(static_content)

        try:
            council = {
                'name': html.xpath('//h2/text()')[0],
                'cassification': u'Council'}
        except IndexError as e:
            council = {}
        organisations.append(council)

        for link in html.xpath('//ul[@class="definitie"][2]//ul//li//a'):
            line = u''.join(link.xpath('.//text()'))
            person, party = [l.strip() for l in line.split(u'\xa0', 1)]
            organisations.append(
                {'name': party[1:-1], 'classification': u'Party'})

        pprint(organisations)

        for item in organisations:
            yield 'application/json', json.dumps(item)
