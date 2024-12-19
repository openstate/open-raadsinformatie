from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.models import *
from ocd_backend.transformers import BaseTransformer
from ocd_backend.settings import AUTORETRY_EXCEPTIONS, RETRY_MAX_RETRIES, AUTORETRY_RETRY_BACKOFF, AUTORETRY_RETRY_BACKOFF_MAX

log = get_source_logger('notubiz_meeting')


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=AUTORETRY_EXCEPTIONS,
                 retry_backoff=AUTORETRY_RETRY_BACKOFF, max_retries=RETRY_MAX_RETRIES, retry_backoff_max=AUTORETRY_RETRY_BACKOFF_MAX)
def meeting_item(self, content_type, raw_item, canonical_iri, cached_path, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']
    
    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'notubiz',
        'collection': 'meeting',
        'canonical_iri': canonical_iri,
        'cached_path': cached_path,
    }

    event = Meeting(original_item['id'], **source_defaults)
    event.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                       source=self.source_definition['key'],
                                                       supplier='allmanak',
                                                       collection=self.source_definition['source_type'])
    event.start_date = original_item['plannings'][0]['start_date']
    event.end_date = original_item['plannings'][0]['end_date']
    event.last_discussed_at = event.start_date
    event.name = original_item['attributes'].get('Titel', 'Vergadering %s' % event.start_date)
    event.classification = ['Agenda']
    event.location = original_item['attributes'].get('Locatie')

    event.organization = TopLevelOrganization(self.source_definition['allmanak_id'],
                                              source=self.source_definition['key'],
                                              supplier='allmanak',
                                              collection=self.source_definition['source_type'])

    if original_item.get('gremium'):
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
                                source=self.source_definition['key'],
                                supplier='notubiz',
                                collection='agenda_item')
        agendaitem.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                source=self.source_definition['key'],
                                                                supplier='allmanak',
                                                                collection=self.source_definition['source_type'])

        try:
            agendaitem.name = item['type_data']['attributes'][0]['value']
        except (KeyError, IndexError):
            try:
                agendaitem.name = item['type_data']['attributes'][1]['value']
            except (KeyError, IndexError):
                pass
        agendaitem.position = original_item['order']
        agendaitem.parent = event
        agendaitem.start_date = event.start_date
        agendaitem.last_discussed_at = event.start_date

        agendaitem.attachment = []
        for doc in item.get('documents', []):
            attachment = MediaObject(doc['id'],
                                     source=self.source_definition['key'],
                                     supplier='notubiz',
                                     collection='attachment')
            attachment.canonical_iri = 'https://' + doc['self'] + '?format=json&version=1.10.8'
            attachment.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                    source=self.source_definition['key'],
                                                                    supplier='allmanak',
                                                                    collection=self.source_definition['source_type'])

            attachment.identifier_url = doc['self']  # Trick to use the self url for enrichment
            attachment.original_url = doc['url']
            attachment.name = doc['title']
            version_def = get_version_definition(doc)
            if version_def:
                attachment.file_name = version_def.get('file_name')
            attachment.date_modified = doc['last_modified']
            attachment.is_referenced_by = agendaitem
            attachment.last_discussed_at = event.start_date
            agendaitem.attachment.append(attachment)

        event.agenda.append(agendaitem)

    # object_model['last_modified'] = iso8601.parse_date(
    #    original_item['last_modified'])

    if 'canceled' in original_item and original_item['canceled']:
        log.info(r'Found a Notubiz event with status EventCancelled: {str(event.values)}')
        event.status = EventCancelled
    elif 'inactive' in original_item and original_item['inactive']:
        log.info(f'Found a Notubiz event with status EventUncomfirmed: {str(event.values)}')
        event.status = EventConfirmed
    else:
        event.status = EventUnconfirmed

    event.attachment = []
    for doc in original_item.get('documents', []):
        attachment = MediaObject(doc['id'],
                                 source=self.source_definition['key'],
                                 supplier='notubiz',
                                 collection='attachment')
        attachment.canonical_iri = 'https://' + doc['url'] + '?format=json&version=1.10.8'
        attachment.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                source=self.source_definition['key'],
                                                                supplier='allmanak',
                                                                collection=self.source_definition['source_type'])

        attachment.identifier_url = doc['self']  # Trick to use the self url for enrichment
        attachment.original_url = doc['url']
        attachment.name = doc['title']
        version_def = get_version_definition(doc)
        if version_def:
            attachment.file_name = version_def.get('file_name')
        attachment.date_modified = doc['last_modified']
        attachment.is_referenced_by = event
        attachment.last_discussed_at = event.start_date
        event.attachment.append(attachment)

    event.save()
    return event

def get_version_definition(doc):
    return filter(lambda version_def: version_def['id'] == doc['version'], doc['versions'])[0]
