import iso8601
import pytz

from ocd_backend import celery_app
from ocd_backend.transformers import BaseTransformer
from ocd_backend.models import *
from ocd_backend.log import get_source_logger

log = get_source_logger('goapi_document')


def get_current_permalink(source_definition, original_item):
    api_version = source_definition.get('api_version', 'v1')
    base_url = '%s/%s' % (
        source_definition['base_url'], api_version,)

    return u'%s/documents/%i' % (base_url, original_item[u'id'],)


def get_documents_as_media_urls(source_definition, original_item, documents):
    current_permalink = get_current_permalink(source_definition, original_item)

    output = []
    for document in documents:
        # sleep(1)
        url = current_permalink
        output.append({
            'url': url,
            'note': document[u'filename']})
    return output


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=(Exception,), retry_backoff=True)
def document_item(self, content_type, raw_item, entity, source_item, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    source_definition = kwargs['source_definition']
    
    source_defaults = {
        'source': source_definition['key'],
        'supplier': 'gemeenteoplossingen',
        'collection': 'document',
    }

    event = Meeting(original_item[u'id'],
                    source_definition,
                    **source_defaults)
    event.entity = entity
    event.has_organization_name = TopLevelOrganization(source_definition['allmanak_id'],
                                                       source=source_definition['key'],
                                                       supplier='allmanak',
                                                       collection='municipality')

    event.organization = TopLevelOrganization(source_definition['allmanak_id'],
                                              source=source_definition['key'],
                                              supplier='allmanak',
                                              collection='municipality')

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
    for doc in get_documents_as_media_urls(source_definition, original_item, original_item.get('documents', [])):
        attachment = MediaObject(doc['url'],
                                 source_definition,
                                 **source_defaults)
        attachment.entity = doc['url']
        attachment.has_organization_name = TopLevelOrganization(source_definition['allmanak_id'],
                                                                source=source_definition['key'],
                                                                supplier='allmanak',
                                                                collection='municipality')

        attachment.identifier_url = doc['url']  # Trick to use the self url for enrichment
        attachment.original_url = doc['url']
        attachment.name = doc['note']
        attachment.isReferencedBy = event
        event.attachment.append(attachment)

    event.save()
    return event
