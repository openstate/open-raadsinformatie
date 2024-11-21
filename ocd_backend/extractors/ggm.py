import json

from ocd_backend.app import celery_app
from ocd_backend.extractors import BaseExtractor
from ocd_backend.log import get_source_logger
from ocd_backend.utils.http import HttpRequestMixin

log = get_source_logger('ggm')
ggm_base_url = 'https://gegevensmagazijn.tweedekamer.nl/'


class GGMBaseExtractor(BaseExtractor, HttpRequestMixin):
    request_url = None

    def __init__(self, source_definition):
        super(GGMBaseExtractor, self).__init__(source_definition=source_definition)

    def run(self):
        assert self.request_url

        skip = celery_app.backend.get(self.request_url)
        if not skip:
            skip = 0

        while True:
            full_url = '{}{}&$skip={}'.format(ggm_base_url, self.request_url, skip)
            _, _, odata_substring = full_url.rpartition(ggm_base_url)

            resource = self.download_url(full_url)

            response_json = json.load(resource.media_file)
            if resource and not resource.from_cache:
                try:
                    items = response_json['value']
                except KeyError:
                    items = [response_json]

                for item in items:
                    if item.get('Verwijderd') is None:
                        # Empty entities where Verwijderd is null instead of false are skipped
                        continue
                    elif item.get('Verwijderd') is True:
                        log.warning('GGM extractor should do a remove request but is not yet implemented')

                    yield 'application/json', json.dumps(item), full_url, 'ggm/' + odata_substring,

                log.debug(f'Processed skip value {skip}')
            else:
                log.debug(f'Already downloaded, skipping value {skip}')

            next_link = response_json.get('@odata.nextLink')
            if next_link:
                _, _, skip = next_link.rpartition('skip=')
                skip = int(skip)

                self.upload(odata_substring, json.dumps(response_json), content_type='application/json')

                celery_app.backend.set(self.request_url, skip)
            else:
                log.info('No next link, stopping')
                break


class GGMMeetingsExtractor(GGMBaseExtractor):
    request_url = 'OData/v4/2.0/Activiteit?$expand=' \
                     'Reservering($expand=Zaal),' \
                     'ActiviteitActor,' \
                     'Document($expand=DocumentActor,Kamerstukdossier),' \
                     'VervangenVanuit,' \
                     'VervangenDoor,' \
                     'Agendapunt($expand=' \
                        'Document($expand=Kamerstukdossier),' \
                        'Besluit($expand=' \
                            'Stemming,' \
                            'Zaak($expand=' \
                                'Document($expand=DocumentActor,Kamerstukdossier),' \
                                'Kamerstukdossier,' \
                                'ZaakActor)))' \
                     '&$format=application%2Fjson;odata.metadata=full'


class GGMPersonExtractor(GGMBaseExtractor):
    request_url = 'OData/v4/2.0/Persoon?&$expand=' \
                  'PersoonContactinformatie,' \
                  'CommissieZetelVastPersoon($expand=CommissieZetel($expand=Commissie)),' \
                  'FractieZetelPersoon($expand=FractieZetel($expand=Fractie))' \
                  '&$format=application%2Fjson;odata.metadata=full'


class GGMCommitteeExtractor(GGMBaseExtractor):
    request_url = 'OData/v4/2.0/Commissie?$expand=' \
                  'CommissieZetel($expand=' \
                        'CommissieZetelVastPersoon($expand=Persoon),' \
                        'CommissieZetelVervangerPersoon($expand=Persoon)),' \
                  'CommissieContactinformatie' \
                  '&$format=application%2Fjson;odata.metadata=full'
