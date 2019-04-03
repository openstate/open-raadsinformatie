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
    Extract persons from an Almanak.
    """

    def extract_items(self, static_content):
        """
        Extracts persons from the Almanak page source HTML.
        """

        html = etree.HTML(static_content)
        persons = []

        for element in html.xpath('//*[@id="functies-organisatie"]/following::table[1]//tr'):
            name = element.xpath('.//a/text()')[0].strip()
            if name.lower() == 'vacant':
                # Exclude vacant positions
                break

            try:
                party = etree.tostring(element).split('(')[1].split(')')[0]
            except:
                # If no party can be extracted, the person is a clerk (griffier). Clerks are not
                # affiliated with a party
                party = None

            url = (u''.join(element.xpath('.//@href'))).strip()
            id = url[1:].split('/')[0]
            email = element.xpath('string(//a[starts-with(@href,"mailto:")]/text())').strip().split(' ')[0]
            gender = u'male' if name.startswith(u'Dhr. ') else u'female'

            if party:
                # Extraction of role requires a HTTP request to a separate page
                request_url = u'https://almanak.overheid.nl%s' % (unicode(url),)
                response = self.http_session.get(request_url, verify=False)
                response.raise_for_status()
                html = etree.HTML(response.content)
                role = html.xpath('//*[@id="basis-medewerker"]/following::table[1]/tr/td/text()')[0].strip()
            else:
                role = 'Griffier'

            persons.append({
                'id': id,
                'name': name,
                'email': email,
                'gender': gender,
                'party': party,
                'role': role,
            })

        for person in persons:
            yield 'application/json', json.dumps(person)
