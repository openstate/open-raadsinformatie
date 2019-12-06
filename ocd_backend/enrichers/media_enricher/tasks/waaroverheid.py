from datetime import datetime

import requests

from ocd_backend.enrichers.media_enricher.tasks import BaseEnrichmentTask
from ocd_backend.log import get_source_logger
from ocd_backend.models.definitions import Geo, NeoGeo
from ocd_backend.models.definitions import schema
from ocd_backend.models.misc import Uri
from ocd_backend.settings import LOCLINKVIS_HOST, LOCLINKVIS_PORT
from ocd_backend.utils.http import HttpRequestMixin

log = get_source_logger('waaroverheid')


class WaarOverheidEnricher(BaseEnrichmentTask, HttpRequestMixin):
    """WaarOverheid Enricher searches for location data in text sources and
    returns which districts, neighborhoods and annotations were mentioned."""
    loclinkvis_url = None

    def enrich_item(self, item, file_object):
        if not isinstance(item, schema.MediaObject):
            return

        if not LOCLINKVIS_HOST or not LOCLINKVIS_PORT:
            # Skip waaroverheid if no host is specified
            return

        self.loclinkvis_url = 'http://{}:{}'.format(LOCLINKVIS_HOST, LOCLINKVIS_PORT)

        cbs_id = self.source_definition.get('cbs_id')
        if not cbs_id:
            # Provinces have no cbs_id and will not be processed
            return

        self.annotate_document(item, cbs_id)

    def annotate_document(self, doc, municipality_code):
        # They're sets because we want to keep duplicates away
        municipal_refs = {
            'districts': set(),
            'neighborhoods': set(),
        }

        field_keys = []
        if isinstance(doc, schema.MediaObject):
            field_keys = ['text']

        if not field_keys:
            return doc

        for field_key in field_keys:
            text = getattr(doc, field_key, '')

            if type(text) == list:
                text = ' '.join(text)

            if not text:
                return

            clean_text = text.replace('-\n', '')
            if clean_text:
                setattr(doc, field_key, clean_text)
            else:
                continue

            url = '{}/annotate'.format(self.loclinkvis_url)
            try:
                resp = self.http_session.post(url, json={
                    'municipality_code': municipality_code,
                    'text': clean_text
                })
            except requests.ConnectionError:
                # Return if no connection can be made
                log.warning('No connection to LocLinkVis: %s' % url)
                return

            if not resp.ok:
                error_dict = {
                    'ori_identifier': doc.get_ori_identifier(),
                    'doc_type': type(doc),
                    'field_key': field_key,
                    'municipality_code': municipality_code,
                    'status_code': resp.status_code,
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                if resp.status_code == 500:
                    error_dict['text'] = clean_text

                log.warn(error_dict)
                continue

            data = resp.json()
            if not data['districts'] and not data['neighborhoods']:
                # No annotations were found, continue
                continue

            municipal_refs['districts'].update(data['districts'])
            municipal_refs['neighborhoods'].update(data['neighborhoods'])

        doc.districts = list(municipal_refs.get('districts'))

        neighborhood_coordinates = list()
        for neighborhood in municipal_refs.get('neighborhoods', []):
            doc.neighborhoods = list(municipal_refs['neighborhoods'])

            url = '{}/municipal/{}'.format(self.loclinkvis_url, neighborhood)
            try:
                resp = self.http_session.get(url)
                resp.raise_for_status()
            except requests.ConnectionError:
                # Return if no connection can be made
                log.warning('No connection to LocLinkVis: %s' % url)
                continue

            json_response = resp.json()
            neighborhood_coordinates.append(json_response['geometry']['coordinates'])

        if neighborhood_coordinates:
            doc.neighborhood_polygons = {
                'type': 'multipolygon',
                'coordinates': neighborhood_coordinates,
            }

            polygons = list()
            for polygon in neighborhood_coordinates:
                pos_list = list()
                for coordinates in polygon[0]:
                    pos_list.append({
                        str(Uri(Geo, 'lat')): coordinates[1],
                        str(Uri(Geo, 'long')): coordinates[0],
                    })

                polygons.append({
                    '@type': str(Uri(NeoGeo, 'Polygon')),
                    str(Uri(NeoGeo, 'exterior')): {
                        '@type': str(Uri(NeoGeo, 'LinearRing')),
                        str(Uri(NeoGeo, 'posList')): pos_list
                    }
                })

            doc.geometry = {
                '@type': str(Uri(NeoGeo, 'MultiPolygon')),
                str(Uri(NeoGeo, 'polygonMember')): polygons,
            }

        return doc
