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

    # 'gremium' may be null in json
    gremium = original_item.get('gremium', {}) or {}
    if gremium.get('id'):
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
        agendaitem.position = item.get('order', '1')
        agendaitem.parent = determine_parent(item, event)
        agendaitem.start_date = event.start_date
        agendaitem.last_discussed_at = event.start_date

        agendaitem.attachment = []
        for doc in item.get('documents', []):
            attachment = create_media_object(self, doc, agendaitem, event.start_date)
            agendaitem.attachment.append(attachment)

        for module_item_contents in item.get('module_item_contents', []):
            for doc in module_item_contents.get('attachments', {}).get('document', []):
                attachment = create_media_object(self, doc, agendaitem, event.start_date)
                agendaitem.attachment.append(attachment)

            module_item_attributes = module_item_contents.get('attributes', [])
            module_item_main_documents = [doc for doc in module_item_attributes if doc["datatype"] == "document" or doc["label"] == "Hoofddocument"]
            if len(module_item_main_documents) == 0:
                # This is ok, a main document is not always present
                message = f'[{self.source_definition["key"]}] no main document for module_item {module_item_contents["id"]}'
                log.info(message)
            elif len(module_item_main_documents) > 1:
                message = f'[{self.source_definition["key"]}] multiple main documents found for module_item {module_item_contents["id"]}'
                log.info(message)
            for module_item_main_document in module_item_main_documents:
                for value in module_item_main_document.get('values', []):
                    doc = value.get('document', {})
                    attachment = create_media_object(self, doc, agendaitem, event.start_date)
                    agendaitem.attachment.append(attachment)

        event.agenda.append(agendaitem)

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
        attachment = create_media_object(self, doc, event, event.start_date)
        event.attachment.append(attachment)

    event.save()
    return event

def determine_parent(item, event):
    parent_dict = item.get('parent')
    if parent_dict == None:
        return event
    parent_id = parent_dict['id']

    # parent agenda_items are processed first, so we should find the parent
    parent = [agendaitem for agendaitem in event.agenda if agendaitem.canonical_id == parent_id][0]
    return parent

def get_version_definition(doc):
    return next(filter(lambda version_def: version_def['id'] == doc['version'], doc['versions']), None)

def create_media_object(self, doc, is_referenced_by, start_date):
    attachment = MediaObject(doc['id'],
                             source=self.source_definition['key'],
                             supplier='notubiz',
                             collection='attachment')
    attachment.canonical_iri = 'https://' + doc['self'] + '?format=json&version=1.17.0'
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

    attachment.is_referenced_by = is_referenced_by
    attachment.last_discussed_at = start_date

    return attachment