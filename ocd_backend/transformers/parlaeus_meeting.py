import re
from datetime import datetime

from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.models import *
from ocd_backend.transformers import BaseTransformer
from ocd_backend.settings import AUTORETRY_EXCEPTIONS, AUTORETRY_MAX_RETRIES, AUTORETRY_RETRY_BACKOFF, AUTORETRY_RETRY_BACKOFF_MAX
from ocd_backend.log import get_source_logger

log = get_source_logger('parlaeus_meeting')

@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=AUTORETRY_EXCEPTIONS,
                 retry_backoff=AUTORETRY_RETRY_BACKOFF, max_retries=AUTORETRY_MAX_RETRIES, retry_backoff_max=AUTORETRY_RETRY_BACKOFF_MAX)
def meeting_item(self, content_type, raw_item, canonical_iri, cached_path, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'parlaeus',
        'collection': 'meeting',
        'canonical_iri': canonical_iri,
        'cached_path': cached_path,
    }

    meeting = Meeting(original_item['agid'], **source_defaults)
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
            attachment.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                    source=self.source_definition['key'],
                                                                    supplier='allmanak',
                                                                    collection=self.source_definition['source_type'])
            attachment.identifier_url = 'parlaeus/agenda_item/%s' % document['dcid']
            attachment.original_url = clean_link(document['link'])
            attachment.name = document.get('title')
            attachment.last_discussed_at = meeting.start_date
            attachment.is_referenced_by = agenda_item

            agenda_item.attachment.append(attachment)

        meeting.agenda.append(agenda_item)

    return meeting

def clean_link(link):
    """
    Some Parlaeus links are wrong and look like e.g.
        https://maastricht.parlaeus.nlhttps://maastricht.parlaeus.nl/user/postin/action=select/start=20241111/end=20241124/ty=262
    Check for this and remove superfluous https://maastricht.parlaeus.nl
    """
    if link == None:
        return

    if re.search("^https://([^.]*).parlaeus.nlhttps://([^.]*).parlaeus.nl", link):
        return re.sub("^https://([^.]*).parlaeus.nl", "", link)

    return link