from ocd_backend import celery_app
from ocd_backend.transformers import BaseTransformer
from ocd_backend.models import *
from ocd_backend.log import get_source_logger

log = get_source_logger('notubiz_meeting')


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=(Exception,), retry_backoff=True)
def meeting_item(self, content_type, raw_item, entity, source_item, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']
    
    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'notubiz',
        'collection': 'meeting',
    }

    event = Meeting(original_item['id'],
                    self.source_definition,
                    **source_defaults)
    event.entity = entity
    event.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                       source=self.source_definition['key'],
                                                       supplier='allmanak',
                                                       collection=self.source_definition['source_type'])
    event.start_date = original_item['plannings'][0]['start_date']
    event.end_date = original_item['plannings'][0]['end_date']
    event.name = original_item['attributes'].get('Titel', 'Vergadering %s' % event.start_date)
    event.classification = [u'Agenda']
    event.location = original_item['attributes'].get('Locatie')

    event.organization = TopLevelOrganization(self.source_definition['allmanak_id'],
                                              source=self.source_definition['key'],
                                              supplier='allmanak',
                                              collection=self.source_definition['source_type'])

    event.committee = Organization(original_item['gremium']['id'],
                                   source=self.source_definition['key'],
                                   supplier='notubiz',
                                   collection='committee')
    event.committee.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                 source=self.source_definition['key'],
                                                                 supplier='allmanak',
                                                                 collection=self.source_definition['source_type'])

    # Re-attach the committee node to the municipality node
    event.committee.subOrganizationOf = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                             source=self.source_definition['key'],
                                                             supplier='allmanak',
                                                             collection=self.source_definition['source_type'])

    event.agenda = []
    for item in original_item.get('agenda_items', []):
        if not item['order']:
            continue

        # If it's a 'label' type skip the item for now, since it only gives little information about what is to come
        if item['type'] == 'label':
            continue

        agendaitem = AgendaItem(item['id'],
                                self.source_definition,
                                source=self.source_definition['key'],
                                supplier='notubiz',
                                collection='agenda_item')
        agendaitem.entity = entity
        agendaitem.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                source=self.source_definition['key'],
                                                                supplier='allmanak',
                                                                collection=self.source_definition['source_type'])

        try:
            agendaitem.description = item['type_data']['attributes'][0]['value']
        except KeyError:
            try:
                agendaitem.description = item['type_data']['attributes'][1]['value']
            except KeyError:
                pass
        agendaitem.name = original_item['attributes']['Titel']
        agendaitem.position = original_item['order']
        agendaitem.parent = event
        agendaitem.start_date = event.start_date

        agendaitem.attachment = []
        for doc in item.get('documents', []):
            attachment = MediaObject(doc['id'],
                                     self.source_definition,
                                     source=self.source_definition['key'],
                                     supplier='notubiz',
                                     collection='attachment')
            attachment.entity = entity
            attachment.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                    source=self.source_definition['key'],
                                                                    supplier='allmanak',
                                                                    collection=self.source_definition['source_type'])

            attachment.identifier_url = doc['self']  # Trick to use the self url for enrichment
            attachment.original_url = doc['url']
            attachment.name = doc['title']
            attachment.date_modified = doc['last_modified']
            attachment.isReferencedBy = agendaitem
            agendaitem.attachment.append(attachment)

        event.agenda.append(agendaitem)

    # object_model['last_modified'] = iso8601.parse_date(
    #    original_item['last_modified'])

    if 'canceled' in original_item and original_item['canceled']:
        log.info('Found a Notubiz event with status EventCancelled: %s' % str(event.values))
        event.status = EventStatus.CANCELLED
    elif 'inactive' in original_item and original_item['inactive']:
        log.info('Found a Notubiz event with status EventUncomfirmed: %s' % str(event.values))
        event.status = EventStatus.CONFIRMED
    else:
        event.status = EventStatus.UNCONFIRMED

    event.attachment = []
    for doc in original_item.get('documents', []):
        attachment = MediaObject(doc['id'],
                                 self.source_definition,
                                 source=self.source_definition['key'],
                                 supplier='notubiz',
                                 collection='attachment')
        attachment.entity = entity
        attachment.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                source=self.source_definition['key'],
                                                                supplier='allmanak',
                                                                collection=self.source_definition['source_type'])

        attachment.identifier_url = doc['self']  # Trick to use the self url for enrichment
        attachment.original_url = doc['url']
        attachment.name = doc['title']
        attachment.date_modified = doc['last_modified']
        attachment.isReferencedBy = event
        event.attachment.append(attachment)

    event.save()
    return event
