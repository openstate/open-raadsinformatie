import iso8601
import pytz

from ocd_backend import celery_app
from ocd_backend.models import *
from ocd_backend.log import get_source_logger
from ocd_backend.transformers.goapi_meeting import GOAPITransformer

log = get_source_logger('goapi_document')


@celery_app.task(bind=True, base=GOAPITransformer, autoretry_for=(Exception,), retry_backoff=True)
def document_item(self, content_type, raw_item, entity, source_item, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']
    
    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'gemeenteoplossingen',
        'collection': 'document',
    }

    event = Meeting(original_item[u'id'],
                    self.source_definition,
                    **source_defaults)
    event.entity = entity
    event.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                       source=self.source_definition['key'],
                                                       supplier='allmanak',
                                                       collection=self.source_definition['source_type'])

    event.organization = TopLevelOrganization(self.source_definition['allmanak_id'],
                                              source=self.source_definition['key'],
                                              supplier='allmanak',
                                              collection=self.source_definition['source_type'])

    try:
        date_tz = pytz.timezone(
            original_item['publicationDate']['timezone'])
    except Exception:
        date_tz = None
    start_date = iso8601.parse_date(
        original_item['publicationDate']['date'].replace(' ', 'T'))
    if date_tz is not None:
        try:
            start_date = start_date.astimezone(date_tz)
        except Exception:
            pass

    event.start_date = start_date
    event.end_date = event.start_date
    event.name = original_item[u'description']
    event.classification = [original_item['documentTypeLabel']]
    event.description = original_item[u'description']

    event.attachment = []
    for doc in self.get_documents_as_media_urls(original_item):
        attachment = MediaObject(doc['url'],
                                 self.source_definition,
                                 **source_defaults)
        attachment.entity = entity
        attachment.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                source=self.source_definition['key'],
                                                                supplier='allmanak',
                                                                collection=self.source_definition['source_type'])

        attachment.identifier_url = doc['url']  # Trick to use the self url for enrichment
        attachment.original_url = doc['url']
        attachment.name = doc['note']
        attachment.isReferencedBy = event
        event.attachment.append(attachment)

    event.save()
    return event
