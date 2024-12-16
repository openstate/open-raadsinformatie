from datetime import datetime
from hashlib import sha1

from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.models import *
from ocd_backend.transformers import BaseTransformer
from ocd_backend.settings import AUTORETRY_EXCEPTIONS, AUTORETRY_MAX_RETRIES, AUTORETRY_RETRY_BACKOFF, AUTORETRY_RETRY_BACKOFF_MAX

log = get_source_logger('greenvalley')


class GreenValleyTransformer(BaseTransformer):
    def __init__(self, *args, **kwargs):
        self.classification_mapping = {
            'agenda': 'Agenda',
            'agendapage': 'Agendapunt',
            'bestuurlijkstuk': 'Bestuurlijk stuk',
            'notule': 'Verslag',
            'ingekomenstuk': 'Ingekomen stuk',
            'antwoordstuk': 'Antwoord'  # ?
        }

    def get_meeting_dates(self, meeting):
        """Determine meeting start and end dates."""

        start_date = None
        end_date = None

        if meeting.get('bis_vergaderdatum', '').strip() != '':
            start_date = datetime.fromtimestamp(
                float(meeting['bis_vergaderdatum']) +
                (float(meeting.get('bis_starttijduren', '0') or '0') * 3600) +
                (float(meeting.get('bis_starttijdminuten', '0') or '0') * 60))
            end_date = datetime.fromtimestamp(
                float(meeting['bis_vergaderdatum']) +
                (float(meeting.get('bis_eindtijduren', '0') or '0') * 3600) +
                (float(meeting.get('bis_eindtijdminuten', '0') or '0') * 60))
        elif 'publishdate' in meeting:
            start_date = datetime.fromtimestamp(
                float(meeting['publishdate']))
            end_date = datetime.fromtimestamp(
                float(meeting['publishdate']))

        return start_date, end_date

    def _get_documents_as_media_urls(self, original_item):
        media_urls = {}
        if 'attachmentlist' in original_item:
            for att_key, att in original_item.get('attachmentlist', {}).items():
                if att['objecttype'] == 'AGENDAPAGE':
                    continue

                url = "https://staten.zuid-holland.nl/dsresource?objectid=%s" % att['objectid']

                doc_hash = sha1(f"{url}:{att['objectname']})".encode('utf-8')).hexdigest()
                media_urls[doc_hash] = {
                    "note": att['objectname'],
                    "original_url": url,
                    "object_id": att['objectid'],
                }
        else:
            default = original_item['default']
            if default['objecttype'] != 'AGENDAPAGE':
                url = "https://staten.zuid-holland.nl/dsresource?objectid=%s" % default['objectid']

                doc_hash = sha1(f"{url}:{default['objectname']})".encode('utf-8')).hexdigest()
                media_urls[doc_hash] = {
                    "note": default['objectname'],
                    "original_url": url,
                    "object_id": default['objectid'],
                }

        if media_urls:
            return media_urls.values()
        else:
            return []
        

@celery_app.task(bind=True, base=GreenValleyTransformer, autoretry_for=AUTORETRY_EXCEPTIONS,
                 retry_backoff=AUTORETRY_RETRY_BACKOFF, max_retries=AUTORETRY_MAX_RETRIES, retry_backoff_max=AUTORETRY_RETRY_BACKOFF_MAX)
def greenvalley_report(self, content_type, raw_item, canonical_iri, cached_path, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']
    
    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'greenvalley',
        'collection': 'report',
        'canonical_iri': canonical_iri,
        'cached_path': cached_path,
    }

    meeting = original_item['default']

    event = Meeting(meeting['objectid'], **source_defaults)
    event.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                       source=self.source_definition['key'],
                                                       supplier='allmanak',
                                                       collection='province')

    event.start_date, event.end_date = self.get_meeting_dates(meeting)
    event.last_discussed_at = event.start_date

    event.name = meeting['objectname']
    event.classification = ['Agenda']
    try:
        event.classification = [self.classification_mapping[meeting['objecttype'].lower()]]
    except LookupError:
        event.classification = [meeting['objecttype'].capitalize()]
    event.description = meeting['objectname']

    try:
        event.location = meeting['bis_locatie'].strip()
    except (AttributeError, KeyError):
        pass

    event.organization = TopLevelOrganization(self.source_definition['allmanak_id'],
                                              source=self.source_definition['key'],
                                              supplier='allmanak',
                                              collection='province')

    if 'bis_orgaan' in meeting:
        if meeting['bis_orgaan'] != '':
            event.committee = Organization(meeting['bis_orgaan'],
                                           source=self.source_definition['key'],
                                           supplier='greenvalley',
                                           collection='committee')
            event.committee.name = meeting['bis_orgaan']
            event.committee.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                         source=self.source_definition['key'],
                                                                         supplier='allmanak',
                                                                         collection='province')
            event.committee.subOrganizationOf = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                     source=self.source_definition['key'],
                                                                     supplier='allmanak',
                                                                     collection='province')

    # object_model['last_modified'] = iso8601.parse_date(
    #    original_item['last_modified'])

    # if original_item['canceled']:
    #     event.status = EventCancelled()
    # elif original_item['inactive']:
    #     event.status = EventUnconfirmed()
    # else:
    #     event.status = EventConfirmed()
    event.status = EventConfirmed

    event.attachment = []
    for doc in self._get_documents_as_media_urls(original_item):
        attachment = MediaObject(doc['object_id'],
                                 source=self.source_definition['key'],
                                 supplier='greenvalley',
                                 collection='attachment')
        attachment.canonical_iri = doc['original_url']
        attachment.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                source=self.source_definition['key'],
                                                                supplier='allmanak',
                                                                collection='province')

        attachment.identifier_url = doc['original_url']  # Trick to use the self url for enrichment
        attachment.original_url = doc['original_url']
        attachment.name = doc['note']
        attachment.is_referenced_by = event
        attachment.last_discussed_at = event.start_date
        event.attachment.append(attachment)

    event.save()
    return event


@celery_app.task(bind=True, base=GreenValleyTransformer, autoretry_for=AUTORETRY_EXCEPTIONS,
                 retry_backoff=AUTORETRY_RETRY_BACKOFF, max_retries=AUTORETRY_MAX_RETRIES, retry_backoff_max=AUTORETRY_RETRY_BACKOFF_MAX)
def meeting_item(self, content_type, raw_item, canonical_iri, cached_path, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']
    
    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'greenvalley',
        'collection': 'meeting',
        'canonical_iri': canonical_iri,
        'cached_path': cached_path,
    }

    meeting = original_item['default']

    event = Meeting(meeting['objectid'], **source_defaults)
    event.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                       source=self.source_definition['key'],
                                                       supplier='allmanak',
                                                       collection='province')

    event.start_date, event.end_date = self.get_meeting_dates(meeting)

    event.name = meeting['objectname']
    event.classification = ['Agenda']
    try:
        event.classification = [self.classification_mapping[meeting['objecttype'].lower()]]
    except LookupError:
        event.classification = [meeting['objecttype'].capitalize()]
    event.description = meeting['objectname']

    try:
        event.location = meeting['bis_locatie'].strip()
    except (AttributeError, KeyError):
        pass

    event.organization = TopLevelOrganization(self.source_definition['allmanak_id'],
                                              source=self.source_definition['key'],
                                              supplier='allmanak',
                                              collection='province')

    if 'bis_orgaan' in meeting:
        if meeting['bis_orgaan'] != '':
            event.committee = Organization(meeting['bis_orgaan'],
                                           source=self.source_definition['key'],
                                           supplier='greenvalley',
                                           collection='committee')
            event.committee.name = meeting['bis_orgaan']
            event.committee.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                         source=self.source_definition['key'],
                                                                         supplier='allmanak',
                                                                         collection='province')
            event.committee.subOrganizationOf = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                     source=self.source_definition['key'],
                                                                     supplier='allmanak',
                                                                     collection='province')

    # object_model['last_modified'] = iso8601.parse_date(
    #    original_item['last_modified'])

    # if original_item['canceled']:
    #     event.status = EventCancelled
    # elif original_item['inactive']:
    #     event.status = EventUnconfirmed
    # else:
    #     event.status = EventConfirmed
    event.status = EventConfirmed

    event.attachment = []
    for doc in self._get_documents_as_media_urls(original_item):
        attachment = MediaObject(doc['original_url'].rpartition('/')[2].split('=')[1],
                                 source=self.source_definition['key'],
                                 supplier='greenvalley',
                                 collection='attachment')
        attachment.canonical_iri = doc['original_url']
        attachment.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                source=self.source_definition['key'],
                                                                supplier='allmanak',
                                                                collection='province')

        attachment.identifier_url = doc['original_url']  # Trick to use the self url for enrichment
        attachment.original_url = doc['original_url']
        attachment.name = doc['note']
        attachment.is_referenced_by = event
        attachment.last_discussed_at = event.start_date
        event.attachment.append(attachment)

    event.agenda = []

    children = []
    for a, v in original_item.get('SETS', {}).items():
        if v['objecttype'].lower() == 'agendapage':
            result = {'default': v}
            children.append(result)

    for item in children:
        agenda_item = item['default']
        agendaitem = AgendaItem(agenda_item['objectid'],
                                source=self.source_definition['key'],
                                supplier='greenvalley',
                                collection='agenda_item')
        agendaitem.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                source=self.source_definition['key'],
                                                                supplier='allmanak',
                                                                collection='province')

        agendaitem.description = agenda_item['objectname']
        agendaitem.name = agenda_item['objectname']
        agendaitem.position = int(agenda_item['agendapagenumber'])
        agendaitem.parent = event
        # AgendaItem requires a start_date because it derives from Meeting
        agendaitem.start_date = event.start_date
        agendaitem.last_discussed_at = event.start_date

        event.agenda.append(agendaitem)

    event.save()
    return event
