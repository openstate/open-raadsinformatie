import iso8601

from ocd_backend import celery_app
from ocd_backend.transformers import BaseTransformer
from ocd_backend.models import *
from ocd_backend.log import get_source_logger

log = get_source_logger('goapi_meeting')


def get_current_permalink(source_definition,original_item):
    api_version = source_definition.get('api_version', 'v1')
    base_url = '%s/%s' % (
        source_definition['base_url'], api_version,)

    return u'%s/meetings/%i' % (base_url, original_item[u'id'],)


def get_documents_as_media_urls(source_definition, original_item, documents):
    current_permalink = get_current_permalink(source_definition, original_item)

    output = []
    for document in documents:
        # sleep(1)
        url = u"%s/documents/%s" % (current_permalink, document['id'])
        output.append({
            'url': url,
            'note': document[u'filename']})
    return output


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=(Exception,), retry_backoff=True)
def meeting_item(self, content_type, raw_item, entity, source_item, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    source_definition = kwargs['source_definition']
    
    source_defaults = {
        'source': source_definition['key'],
        'supplier': 'gemeenteoplossingen',
        'collection': 'meeting',
    }

    event = Meeting(original_item[u'id'],
                    source_definition,
                    **source_defaults)
    event.entity = entity
    event.has_organization_name = TopLevelOrganization(source_definition['allmanak_id'],
                                                       source=source_definition['key'],
                                                       supplier='allmanak',
                                                       collection='governmental_organization')

    # dates in v1 have a time in them and in v2 they don't
    if ':' in original_item['date']:
        start_date = original_item['date']
    else:
        start_date = "%sT%s:00" % (
            original_item['date'],
            original_item.get('startTime', '00:00',))

    event.start_date = iso8601.parse_date(start_date)
    event.end_date = event.start_date  # ?

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
    event.organization = TopLevelOrganization(source_definition['allmanak_id'],
                                              source=source_definition['key'],
                                              supplier='allmanak',
                                              collection='governmental_organization')

    # Attach the meeting to the committee node. GO always lists either the name of the committee or 'Raad'
    # if it is a non-committee meeting so we can attach it to a committee node without any extra checks.
    event.committee = Organization(original_item[u'dmu'][u'id'],
                                   source=source_definition['key'],
                                   supplier='gemeenteoplossingen',
                                   collection='committee')
    event.committee.has_organization_name = TopLevelOrganization(source_definition['allmanak_id'],
                                                                 source=source_definition['key'],
                                                                 supplier='allmanak',
                                                                 collection='governmental_organization')
    event.committee.subOrganizationOf = TopLevelOrganization(source_definition['allmanak_id'],
                                                             source=source_definition['key'],
                                                             supplier='allmanak',
                                                             collection='governmental_organization')

    # object_model['last_modified'] = iso8601.parse_date(
    #    original_item['last_modified'])

    # TODO: This is untested so we log any cases that are not the default
    if 'canceled' in original_item and original_item['canceled']:
        log.info('Found a GOAPI event with status EventCancelled: %s' % str(event.values))
        event.status = EventStatus.CANCELLED
    elif 'inactive' in original_item and original_item['inactive']:
        log.info('Found a GOAPI event with status EventUnconmfirmed: %s' % str(event.values))
        event.status = EventStatus.UNCONFIRMED
    else:
        event.status = EventStatus.CONFIRMED

    event.agenda = []
    for item in original_item.get('items', []):
        if not item['sortorder']:
            continue

        agendaitem = AgendaItem(item['id'],
                                source_definition,
                                source=source_definition['key'],
                                supplier='gemeenteoplossingen',
                                collection='agenda_item')
        agendaitem.entity = entity
        agendaitem.has_organization_name = TopLevelOrganization(source_definition['allmanak_id'],
                                                                source=source_definition['key'],
                                                                supplier='allmanak',
                                                                collection='governmental_organization')

        agendaitem.__rel_params__ = {'rdf': '_%i' % item['sortorder']}
        agendaitem.description = item['description']
        agendaitem.name = '%s: %s' % (item['number'], item['title'],)
        agendaitem.position = item['sortorder']
        agendaitem.parent = event
        agendaitem.start_date = event.start_date
        agendaitem.attachment = []

        for doc in get_documents_as_media_urls(source_definition, original_item, item.get('documents', [])):
            attachment = MediaObject(doc['url'].rpartition('/')[2],
                                     source_definition,
                                     source=source_definition['key'],
                                     supplier='gemeenteoplossingen',
                                     collection='attachment')
            attachment.entity = doc['url']
            attachment.has_organization_name = TopLevelOrganization(source_definition['allmanak_id'],
                                                                    source=source_definition['key'],
                                                                    supplier='allmanak',
                                                                    collection='governmental_organization')

            attachment.identifier_url = doc['url']  # Trick to use the self url for enrichment
            attachment.original_url = doc['url']
            attachment.name = doc['note']
            attachment.isReferencedBy = agendaitem
            agendaitem.attachment.append(attachment)

        event.agenda.append(agendaitem)

    event.attachment = []
    for doc in get_documents_as_media_urls(source_definition, original_item, original_item.get('documents', [])):
        attachment = MediaObject(doc['url'].rpartition('/')[2],
                                 source_definition,
                                 source=source_definition['key'],
                                 supplier='gemeenteoplossingen',
                                 collection='attachment')
        attachment.entity = doc['url']
        attachment.has_organization_name = TopLevelOrganization(source_definition['allmanak_id'],
                                                                source=source_definition['key'],
                                                                supplier='allmanak',
                                                                collection='governmental_organization')

        attachment.identifier_url = doc['url']  # Trick to use the self url for enrichment
        attachment.original_url = doc['url']
        attachment.name = doc['note']
        attachment.isReferencedBy = event
        event.attachment.append(attachment)

    event.save()
    return event
