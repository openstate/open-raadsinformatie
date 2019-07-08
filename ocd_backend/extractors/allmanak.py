import json
from urlparse import urljoin

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
        self.base_url = '%s/%s/' % ('https://rest-api.allmanak.nl:443', self.source_definition['allmanak_api_version'],)

    def _request(self, path):
        # log.debug('Now retrieving: %s' % (urljoin(self.base_url, path),))
        response = self.http_session.get(urljoin(self.base_url, path), verify=False)

        if response.status_code == 200:
            static_json = json.loads(response.content)
            return len(static_json), static_json
        else:
            log.error('[%s] Failed to extract from Allmanak path %s' % (
                self.source_definition['sitename'], urljoin(self.base_url, path))
                      )
            return 0, []


class AllmanakMunicipalityExtractor(AllmanakBaseExtractor):
    """
    Extracts a municipality from the OpenState Allmanak. There should always be exactly 1 result.
    """

    def run(self):
        path = self.base_url + 'overheidsorganisatie?systemid=eq.%s' % self.source_definition['allmanak_id']

        total, static_json = self._request(path)

        if total != 1:
            log.error('[%s] Number of extracted municipalities for %s is not equal to 1' % (
                self.source_definition['sitename'],
                self.source_definition['sitename'])
                      )
        else:
            yield 'application/json', \
                  json.dumps(static_json[0]), \
                  path, \
                  static_json
            log.info("[%s] Extracted 1 Allmanak municipality." % self.source_definition['sitename'])


class AllmanakProvinceExtractor(AllmanakBaseExtractor):
    """
    Extracts a province from the OpenState Allmanak. There should always be exactly 1 result.
    """

    def run(self):
        path = self.base_url + 'overheidsorganisatie?systemid=eq.%s' % self.source_definition['allmanak_id']

        total, static_json = self._request(path)

        if total != 1:
            log.error('[%s] Number of extracted provinces for %s is not equal to 1' % (
                self.source_definition['sitename'],
                self.source_definition['sitename'])
                      )
        else:
            yield 'application/json', \
                  json.dumps(static_json[0]), \
                  path, \
                  static_json
            log.info("[%s] Extracted 1 Allmanak province." % self.source_definition['sitename'])


class AllmanakPartiesExtractor(AllmanakBaseExtractor):
    """
    Extracts parties from the OpenState Allmanak.
    """

    def run(self):
        path = self.base_url + 'overheidsorganisatie?systemid=eq.%s&select=zetels' % self.source_definition['allmanak_id']

        total, static_json = self._request(path)

        if static_json[0]['zetels']:
            total_parties = 0
            for party in static_json[0]['zetels']:
                yield 'application/json', \
                      json.dumps(party), \
                      path, \
                      static_json
                total_parties += 1
            log.info("[%s] Extracted %d Allmanak parties." % (self.source_definition['sitename'], total_parties))
        else:
            log.warning('[%s] Allmanak does not list any parties for this source.' % self.source_definition['sitename'])


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
            total_persons = 0
            for person in static_json[0]['functies'][4]['functie']['medewerkers']:
                yield 'application/json', \
                      json.dumps(person['persoon']), \
                      path, \
                      static_json
                total_persons += 1
            log.info("[%s] Extracted %d Allmanak persons." % (self.source_definition['sitename'], total_persons))
        else:
            log.warning('[%s] Allmanak does not list any persons for this source.' % self.source_definition['sitename'])
