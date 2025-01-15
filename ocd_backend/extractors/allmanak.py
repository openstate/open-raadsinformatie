import json
from urllib.parse import urljoin

from ocd_backend.extractors import BaseExtractor
from ocd_backend.log import get_source_logger
from ocd_backend.utils.http import HttpRequestMixin


log = get_source_logger('extractor')


class AllmanakBaseExtractor(BaseExtractor, HttpRequestMixin):
    """
    A base extractor for the OpenState Allmanak API.
    """

    def __init__(self, *args, **kwargs):
        super(AllmanakBaseExtractor, self).__init__(*args, **kwargs)
        self.base_url = '%s/%s/' % ('https://rest-api.allmanak.nl', self.source_definition['allmanak_api_version'],)

    def _request(self, path):
        # log.debug('Now retrieving: %s' % (urljoin(self.base_url, path),))
        response = self.http_session.get(urljoin(self.base_url, path), verify=False)

        if response.status_code == 200:
            static_json = json.loads(response.content)
            return len(static_json), static_json
        else:
            log.error(f'[{self.source_definition["key"]}] Failed to extract from Allmanak path '
                      f'{urljoin(self.base_url, path)}')
            return 0, []


class AllmanakMunicipalityExtractor(AllmanakBaseExtractor):
    """
    Extracts a municipality from the OpenState Allmanak. There should always be exactly 1 result.
    """

    def run(self):
        path = self.base_url + 'overheidsorganisatie?systemid=eq.%s' % self.source_definition['allmanak_id']

        total, static_json = self._request(path)

        if total != 1:
            log.error(f'[{self.source_definition["key"]}] Number of extracted municipalities is not equal to 1 (it is {total})')
        else:
            hash_for_item = self.hash_for_item('allmanak', self.source_definition['allmanak_id'], 'municipality', self.source_definition['allmanak_id'], static_json[0])
            if hash_for_item:
                yield 'application/json', \
                      json.dumps(static_json[0]), \
                      path, \
                      None, \
                      hash_for_item
                log.info(f'[{self.source_definition["key"]}] Extracted 1 Allmanak municipality.')
            else:
                log.info(f'[{self.source_definition["key"]}] Skipped 1 Allmanak municipality.')

class AllmanakProvinceExtractor(AllmanakBaseExtractor):
    """
    Extracts a province from the OpenState Allmanak. There should always be exactly 1 result.
    """

    def run(self):
        path = self.base_url + 'overheidsorganisatie?systemid=eq.%s' % self.source_definition['allmanak_id']

        total, static_json = self._request(path)

        if total != 1:
            log.error(f'[{self.source_definition["key"]}] Number of extracted provinces is not equal to 1')
        else:
            hash_for_item = self.hash_for_item('allmanak', self.source_definition['allmanak_id'], 'province', self.source_definition['allmanak_id'], static_json[0])
            if hash_for_item:
                yield 'application/json', \
                      json.dumps(static_json[0]), \
                      path, \
                      None, \
                      hash_for_item
                log.info(f'[{self.source_definition["key"]}] Extracted 1 Allmanak province.')
            else:
                log.info(f'[{self.source_definition["key"]}] Skipped 1 Allmanak province.')


class AllmanakPartiesExtractor(AllmanakBaseExtractor):
    """
    Extracts parties from the OpenState Allmanak.
    """

    def run(self):
        path = self.base_url + 'overheidsorganisatie?systemid=eq.%s&select=zetels' % self.source_definition['allmanak_id']

        total, static_json = self._request(path)

        if static_json[0]['zetels']:
            hash_for_item = self.hash_for_item('allmanak', self.source_definition['allmanak_id'], 'parties', self.source_definition['allmanak_id'], static_json[0]['zetels'])
            if hash_for_item:
                total_parties = 0
                for party in static_json[0]['zetels']:
                    yield 'application/json', \
                          json.dumps(party), \
                          path, \
                          None, \
                          hash_for_item
                    total_parties += 1
                log.info(f'[{self.source_definition["key"]}] Extracted {total_parties} Allmanak parties.')
            else:
                log.info(f'[{self.source_definition["key"]}] Skipped Allmanak parties.')
        else:
            log.warning(f'[{self.source_definition["key"]}] Allmanak does not list any parties for this source.')


class AllmanakPersonsExtractor(AllmanakBaseExtractor):
    """
    Extracts persons from the OpenState Allmanak.
    """

    def run(self):
        path = self.base_url + 'overheidsorganisatie?systemid=eq.%s&select=naam,functies(functie:functieid' \
                               '(naam,medewerkers(persoon:persoonid(systemid,naam,partij))))' \
                               '&functies.functie.naam=eq.Raadslid' % self.source_definition['allmanak_id']

        total, static_json = self._request(path)

        if static_json[0]['functies']:
            hash_for_item = self.hash_for_item('allmanak', self.source_definition['allmanak_id'], 'persons', self.source_definition['allmanak_id'], static_json[0]['functies'])
            if hash_for_item:
                total_persons = 0
                for row in static_json[0]['functies']:
                    if row['functie']:
                        for person in row['functie']['medewerkers']:
                            yield 'application/json', \
                                  json.dumps(person['persoon']), \
                                  path, \
                                  None, \
                                  hash_for_item
                            total_persons += 1
                log.info(f'[{self.source_definition["key"]}] Extracted {total_persons} Allmanak persons.')
            else:
                log.info(f'[{self.source_definition["key"]}] Skipped Allmanak persons.')
        else:
            log.warning(f'[{self.source_definition["key"]}] Allmanak does not list any persons for this source.')
