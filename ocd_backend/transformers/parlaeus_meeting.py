from datetime import datetime

from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.models import *
from ocd_backend.transformers import BaseTransformer


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def meeting_item(self, content_type, raw_item, entity, source_item, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'parlaeus',
        'collection': 'meeting',
    }

    meeting = Meeting(original_item['agid'], **source_defaults)
    meeting.canonical_iri = entity
    meeting.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                         source=self.source_definition['key'],
                                                         supplier='allmanak',
                                                         collection=self.source_definition['source_type'])
    meeting.organization = meeting.has_organization_name

    meeting.name = original_item.get('title')
    meeting.description = original_item.get('description')
    meeting.location = original_item.get('location')
    meeting.chair = original_item.get('chairman')

    meeting.committee = Organization(original_item['cmid'], **source_defaults)

    if original_item.get('time'):
        meeting.start_date = datetime.strptime(
            '%s %s' % (original_item['date'], original_item['time']),
            '%Y%m%d %H:%M'
        )
        meeting.last_discussed_at = meeting.start_date

    if original_item.get('endtime') and original_item['endtime'] != '0':
        meeting.end_date = datetime.strptime(
            '%s %s' % (original_item['date'], original_item['endtime']),
            '%Y%m%d %H:%M'
        )

    meeting.status = EventConfirmed

    # In the past they have assigned cancelled items to a committee
    if original_item['cancelled'] != 0:
        meeting.status = EventCancelled

    meeting.agenda = list()
    for item in original_item.get('points'):
        agenda_item = AgendaItem(item['apid'], **source_defaults)
        agenda_item.canonical_id = item['apid']
        agenda_item.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                 source=self.source_definition['key'],
                                                                 supplier='allmanak',
                                                                 collection=self.source_definition['source_type'])

        agenda_item.parent = meeting
        agenda_item.name = item.get('title')
        agenda_item.start_date = meeting.start_date
        agenda_item.last_discussed_at = meeting.start_date

        if item.get('text'):
            agenda_item.description = item['text']

        agenda_item.attachment = list()
        for document in item.get('documents', []):
            attachment = MediaObject(document['dcid'], **source_defaults)
            attachment.canonical_id = document['dcid']
            attachment.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                    source=self.source_definition['key'],
                                                                    supplier='allmanak',
                                                                    collection=self.source_definition['source_type'])
            attachment.identifier_url = 'parlaeus/agenda_item/%s' % document['dcid']
            attachment.original_url = document['link']
            attachment.name = document.get('title')
            attachment.last_discussed_at = meeting.start_date
            attachment.is_referenced_by = agenda_item

            agenda_item.attachment.append(attachment)

        meeting.agenda.append(agenda_item)

    return meeting
