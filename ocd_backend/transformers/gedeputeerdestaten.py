from datetime import datetime
from urlparse import urljoin

import requests

from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.models import *
from ocd_backend.transformers import BaseTransformer

log = get_source_logger('gedeputeerdestaten')


class GedeputeerdeStatenTransformer(BaseTransformer):
    def __init__(self, *args, **kwargs):
        self.date_mapping = {
            'januari': '01',
            'februari': '02',
            'maart': '03',
            'april': '04',
            'mei': '05',
            'juni': '06',
            'juli': '07',
            'augustus': '08',
            'september': '09',
            'oktober': '10',
            'november': '11',
            'december': '12',
        }

    def get_meeting_date(self, nl_date_str):
        result = nl_date_str
        for m, n in self.date_mapping.iteritems():
            result = result.replace('%s' % (m,), n)
        result = result.strip().replace(' ', '-')
        if len(result) < 10:
            result = '0' + result
        return datetime.strptime(result, '%d-%m-%Y')

    def _get_documents_as_media_urls(self, details):
        media_urls = []

        details_url = details.xpath('//meta[contains(@property, "og:url")]/@content')[0]
        for node in details.xpath('//a[contains(@class, "importLink")]'):
            media_urls.append({
                'note': u''.join(node.xpath('.//text()')),
                'original_url': urljoin(details_url, node.xpath('./@href')[0])
            })
        return media_urls


@celery_app.task(bind=True, base=GedeputeerdeStatenTransformer, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def gs_meeting_item(self, content_type, raw_item, entity, source_item, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'greenvalley',
        'collection': 'meeting',
    }

    original_id = unicode(original_item.xpath(self.source_definition['item_id_xpath'])[0])

    try:
        content = requests.get(original_id).content
    except Exception as e:
        log.error(e)
        content = u''

    if content == '':
        log.erorr('Could not get detailed gedeputeerde staten page')
        return

    province = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                       source=self.source_definition['key'],
                                                       supplier='allmanak',
                                                       collection='province')
    details = self.deserialize_item('application/html', content)

    event = Meeting(original_id, **source_defaults)
    event.canonical_id = original_id
    event.has_organization_name = province

    raw_datum_str = u''.join(
        details.xpath('//div[contains(@class, "type-meta")]//text()')).split(':')[-1]
    clean_date_str = self.get_meeting_date(raw_datum_str)
    event.start_date = event.end_date = clean_date_str
    event.last_discussed_at = event.start_date

    event.name = u''.join(details.xpath('//h1//text()'))
    event.classification = [u'GS-Besluit']
    event.description = u''.join(details.xpath('//div[contains(@class, "type-inhoud")]//text()'))

    event.organization = province

    event.status = EventConfirmed

    event.attachment = []

    for doc in self._get_documents_as_media_urls(details):
        attachment = MediaObject(doc['original_url'],
                                 source=self.source_definition['key'],
                                 supplier=self.source_definition.get('supplier', self.source_definition['key']),
                                 collection='attachment')
        attachment.canonical_iri = doc['original_url']
        attachment.has_organization_name = province

        attachment.identifier_url = doc['original_url']  # Trick to use the self url for enrichment
        attachment.original_url = doc['original_url']
        attachment.name = doc['note']
        attachment.isReferencedBy = event
        attachment.last_discussed_at = event.start_date
        event.attachment.append(attachment)

    event.save()
    return event
