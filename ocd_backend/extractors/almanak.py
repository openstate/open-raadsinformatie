import json

from lxml import etree

from ocd_backend.log import get_source_logger
from .staticfile import StaticHtmlExtractor

log = get_source_logger('extractor')


class OrganisationsExtractor(StaticHtmlExtractor):
    """
    Extract organisations (parties) from an Almanak.
    """

    def extract_items(self, static_content):
        """
        Extracts organisations from the Almanak page source HTML.
        """

        organisations = {}
        html = etree.HTML(static_content)

        # Parties are listed in TR's in the first TABLE after the H2 element with id 'functies-organisatie'
        for element in html.xpath('//*[@id="functies-organisatie"]/following::table[1]//tr'):
            try:
                # Extract the party name from within the "(" and ")" characters
                party = etree.tostring(element).split('(')[1].split(')')[0]
                organisations[party] = ({'name': party, 'classification': u'Party'})
            except:
                pass

        for item in organisations.values():
            yield 'application/json', json.dumps(item)


class PersonsExtractor(StaticHtmlExtractor):
    """
    Extract persons from an Almanak
    """

    def extract_items(self, static_content):
        """
        Extracts persons from a HTML file. Also passes parties to the item
        transformer.
        """

        html = etree.HTML(static_content)
        municipality = u''.join(html.xpath('//div[@id="content"]//h2/text()')).strip()

        for person in html.xpath('//ul[@class="definitie"][2]//ul//li//a'):
            person_url = (u''.join(person.xpath('.//@href'))).strip()
            person_text = (u''.join(person.xpath('.//text()'))).strip()
            person_id = person_url[1:].split('/')[0]

            if person_url != '':
                # TODO: fields are not the best, but hey :)
                yield 'application/json', json.dumps({
                    'id': person_id,
                    'url': person_url,
                    'text': person_text,
                    'municipality': municipality
                })
