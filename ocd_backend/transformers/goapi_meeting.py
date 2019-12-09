import iso8601

from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.models import *
from ocd_backend.transformers import BaseTransformer

log = get_source_logger('goapi_meeting')


class GOAPITransformer(BaseTransformer):
    def get_current_permalink(self, original_item):
        api_version = self.source_definition.get('api_version', 'v1')
        base_url = '%s/%s' % (
            self.source_definition['base_url'], api_version,)

        return u'%s/meetings/%i' % (base_url, original_item[u'id'],)

    def get_documents_as_media_urls(self, original_item):
        current_permalink = self.get_current_permalink(original_item)

        output = []
        for document in original_item.get('documents', []):
            # sleep(1)
            url = u"%s/documents/%s" % (current_permalink, document['id'])
            output.append({
                'url': url,
                'note': document[u'filename']})
        return output


# noinspection DuplicatedCode
@celery_app.task(bind=True, base=GOAPITransformer, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def meeting_item(self, content_type, raw_item, canonical_iri, cached_path, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']
    
    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'gemeenteoplossingen',
        'collection': 'meeting',
        'canonical_iri': canonical_iri,
        'cached_path': cached_path,
    }

    event = Meeting(original_item[u'id'], **source_defaults)
    event.canonical_id = original_item[u'id']
    event.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                       source=self.source_definition['key'],
                                                       supplier='allmanak',
                                                       collection=self.source_definition['source_type'])

    # dates in v1 have a time in them and in v2 they don't
    if ':' in original_item['date']:
        start_date = original_item['date']
    else:
        start_date = "%sT%s:00" % (
            original_item['date'],
            original_item.get('startTime', '00:00',))

    event.start_date = iso8601.parse_date(start_date)
    event.end_date = event.start_date  # ?
    event.last_discussed_at = event.start_date

    # Some meetings are missing a name because some municipalities do not always fill the description field.
    # In this case we create the name from the name of the commission and the start date of the meeting.
    # See issue #124.
    if original_item['description'] == '':
        event.name = 'Vergadering - %s - %s' % (original_item[u'dmu'][u'name'], event.start_date)
    else:
        event.name = original_item[u'description']

    event.classification = [u'Agenda']
    event.description = original_item[u'description']

    try:
        event.location = original_item[u'location'].strip()
    except (AttributeError, KeyError):
        pass

    # Attach the meeting to the municipality node
    event.organization = TopLevelOrganization(self.source_definition['allmanak_id'],
                                              source=self.source_definition['key'],
                                              supplier='allmanak',
                                              collection=self.source_definition['source_type'])

    # Attach the meeting to the committee node. GO always lists either the name of the committee or 'Raad'
    # if it is a non-committee meeting so we can attach it to a committee node without any extra checks.
    event.committee = Organization(original_item[u'dmu'][u'id'],
                                   source=self.source_definition['key'],
                                   supplier='gemeenteoplossingen',
                                   collection='committee')
    event.committee.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                 source=self.source_definition['key'],
                                                                 supplier='allmanak',
                                                                 collection=self.source_definition['source_type'])
    event.committee.subOrganizationOf = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                             source=self.source_definition['key'],
                                                             supplier='allmanak',
                                                             collection=self.source_definition['source_type'])

    # object_model['last_modified'] = iso8601.parse_date(
    #    original_item['last_modified'])

    # TODO: This is untested so we log any cases that are not the default
    if 'canceled' in original_item and original_item['canceled']:
        log.info('Found a GOAPI event with status EventCancelled: %s' % str(event.values))
        event.status = EventCancelled
    elif 'inactive' in original_item and original_item['inactive']:
        log.info('Found a GOAPI event with status EventUnconmfirmed: %s' % str(event.values))
        event.status = EventUnconfirmed
    else:
        event.status = EventConfirmed

    event.agenda = []
    for item in original_item.get('items', []):
        if not item['sortorder']:
            continue

        agendaitem = AgendaItem(item['id'],
                                source=self.source_definition['key'],
                                supplier='gemeenteoplossingen',
                                collection='agenda_item')
        agendaitem.canonical_id = item['id']
        agendaitem.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                source=self.source_definition['key'],
                                                                supplier='allmanak',
                                                                collection=self.source_definition['source_type'])

        agendaitem.description = item['description']
        agendaitem.name = '%s: %s' % (item['number'], item['title'],)
        agendaitem.position = item['sortorder']
        agendaitem.parent = event
        agendaitem.start_date = event.start_date
        agendaitem.last_discussed_at = event.start_date
        agendaitem.attachment = []

        for doc in self.get_documents_as_media_urls(original_item):
            attachment = MediaObject(doc['url'].rpartition('/')[2],
                                     source=self.source_definition['key'],
                                     supplier='gemeenteoplossingen',
                                     collection='attachment')
            attachment.canonical_iri = doc['url']
            attachment.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                    source=self.source_definition['key'],
                                                                    supplier='allmanak',
                                                                    collection=self.source_definition['source_type'])

            attachment.identifier_url = doc['url']  # Trick to use the self url for enrichment
            attachment.original_url = doc['url']
            attachment.name = doc['note']
            attachment.is_referenced_by = agendaitem
            attachment.last_discussed_at = event.start_date
            agendaitem.attachment.append(attachment)

        event.agenda.append(agendaitem)

    event.attachment = []
    for doc in self.get_documents_as_media_urls(original_item):
        attachment = MediaObject(doc['url'].rpartition('/')[2],
                                 source=self.source_definition['key'],
                                 supplier='gemeenteoplossingen',
                                 collection='attachment')
        attachment.canonical_iri = doc['url']
        attachment.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                source=self.source_definition['key'],
                                                                supplier='allmanak',
                                                                collection=self.source_definition['source_type'])

        attachment.identifier_url = doc['url']  # Trick to use the self url for enrichment
        attachment.original_url = doc['url']
        attachment.name = doc['note']
        attachment.is_referenced_by = event
        attachment.last_discussed_at = event.start_date
        event.attachment.append(attachment)

    event.save()
    return event
