import subprocess

import requests

from ocd_backend.enrichers.text_enricher.tasks import BaseEnrichmentTask
from ocd_backend.exceptions import SkipEnrichment
from ocd_backend.models.definitions import schema
from ocd_backend.log import get_source_logger
from ocd_backend.settings import TAPI_DOCUMENT_LIST_URL
from ocd_backend.utils.oauth import OauthMixin

log = get_source_logger('hieroverheid')


class HierOverheidUploader(BaseEnrichmentTask, OauthMixin):

    def enrich_item(self, item):
        if not isinstance(item, schema.MediaObject):
            return

        doc_id = item.get_short_identifier()
        if not doc_id:
            SkipEnrichment('item {} does not have an ori_id'.format(item))
        elif not hasattr(item, 'text_pages'):
            SkipEnrichment('orid:{} text has not been split into pages'.format(doc_id))
        elif not item.text_pages:
            SkipEnrichment('orid:{} is missing text; is it a MediaObject?'.format(doc_id))

        doc_orid = 'orid:{}'.format(doc_id)  # hardcoded prefix for TAPI compatibility
        tapi_data = {
            'document_id': doc_orid,
            'title': item.name,
            'sections': [
                {
                    'heading': 'page {}'.format(page['page_number']),
                    'body': page['text'].strip() or '---'
                }
                for page in item.text_pages[:5000]
            ]
        }

        tapi_url = TAPI_DOCUMENT_LIST_URL + '{}/'.format(doc_orid)
        try:
            head_resp = self.oauth_session.head(tapi_url)
            if not head_resp.ok:  # only PUT the doc if it isn't there yet
                resp = self.oauth_session.put(tapi_url, json=tapi_data)
                if not resp.ok:
                    log.warning('PUT {}: {} {}'.format(tapi_url, resp.status_code, resp.text))
                resp.raise_for_status()

            try:
                hoard_log = subprocess.check_output(
                    [
                        'python3',
                        '-u',
                        '/opt/ori/hieroverheid-base-master/make_abbreviation_hoards.py',
                        doc_id
                    ],
                    stderr=subprocess.STDOUT,
                )
                log.info('make_abbreviation_hoards.py succeeded:\n{}'.format(hoard_log))
            except subprocess.CalledProcessError as e:
                log.warning('make_abbreviation_hoards.py failed: {}'.format(e.output))
                raise
        except requests.ConnectionError:
            log.warning('No connection to TAPI for PUT {}'.format(tapi_url))
