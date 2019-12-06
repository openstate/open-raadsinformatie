import operator
import requests

from ocd_backend.enrichers.text_enricher.tasks import BaseEnrichmentTask
from ocd_backend.models.definitions import Meeting as MeetingNS, Rdf
from ocd_backend.models.misc import Uri
from ocd_backend.settings import ORI_CLASSIFIER_HOST, ORI_CLASSIFIER_PORT
from ocd_backend.utils.http import HttpRequestMixin
from ocd_backend.log import get_source_logger

log = get_source_logger('theme_classifier')


class ThemeClassifier(BaseEnrichmentTask, HttpRequestMixin):
    def enrich_item(self, item):
        if not ORI_CLASSIFIER_HOST or not ORI_CLASSIFIER_PORT:
            # Skip classifier if no host is specified
            return

        ori_classifier_url = 'http://{}:{}/classificeer'.format(ORI_CLASSIFIER_HOST, ORI_CLASSIFIER_PORT)

        if not hasattr(item, 'text'):
            return

        text = item.text
        if type(item.text) == list:
            text = ' '.join(text)

        if not text or len(text) < 76:
            return

        identifier_key = 'result'
        request_json = {
            'ori_identifier': identifier_key,  # not being used
            'name': text
        }

        try:
            response = self.http_session.post(ori_classifier_url, json=request_json)
            response.raise_for_status()
        except requests.ConnectionError:
            # Return if no connection can be made
            log.warning('No connection to theme classifier')
            return

        response_json = response.json()

        theme_classifications = response_json.get(identifier_key, [])

        # Do not try this at home
        tags = {
            '@id': '%s#tags' % item.get_ori_identifier(),
            '@type': str(Uri(Rdf, 'Seq'))
        }
        i = 0
        for name, value in sorted(theme_classifications.items(), key=operator.itemgetter(1), reverse=True):
            tag = {
                '@id': '%s#tags_%s' % (item.get_ori_identifier(), i),
                '@type': str(Uri(MeetingNS, 'TagHit')),
                str(Uri(MeetingNS, 'tag')): name,
                str(Uri(MeetingNS, 'score')): value,
            }

            tags[str(Uri(Rdf, '_%s' % i))] = tag
            i += 1
        # No really, don't

        item.tags = tags
