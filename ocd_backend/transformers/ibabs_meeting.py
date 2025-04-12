import iso8601

from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.models import *
from ocd_backend.transformers import BaseTransformer
from ocd_backend.utils.ibabs import translate_position
from ocd_backend.settings import AUTORETRY_EXCEPTIONS, RETRY_MAX_RETRIES, AUTORETRY_RETRY_BACKOFF, AUTORETRY_RETRY_BACKOFF_MAX

log = get_source_logger('ibabs_meeting')


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=AUTORETRY_EXCEPTIONS,
                 retry_backoff=AUTORETRY_RETRY_BACKOFF, max_retries=RETRY_MAX_RETRIES, retry_backoff_max=AUTORETRY_RETRY_BACKOFF_MAX)
def meeting_item(self, content_type, raw_item, canonical_iri, cached_path, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'ibabs',
        'collection': 'meeting',
        'cached_path': cached_path,
    }

    # Sometimes the meeting is contained in a sub-dictionary called 'Meeting'
    if 'Meeting' in original_item:
        meeting = original_item['Meeting']
    else:
        meeting = original_item

    item = Meeting(meeting['Id'], **source_defaults)
    item.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                      source=self.source_definition['key'],
                                                      supplier='allmanak',
                                                      collection=self.source_definition['source_type'])

    item.name = meeting['Meetingtype']
    item.description = meeting['Explanation']
    item.chair = meeting['Chairman']
    item.location = meeting['Location']
    item.start_date = iso8601.parse_date(meeting['MeetingDate'], ).strftime("%s")
    item.last_discussed_at = item.start_date

    # TODO: This is untested so we log any cases that are not the default
    if 'canceled' in meeting and meeting['canceled']:
        log.info(f'[{self.source_definition["key"]}] Found an iBabs event with status EventCancelled: {str(item.values)}')
        item.status = EventCancelled
    elif 'inactive' in meeting and meeting['inactive']:
        log.info(f'[{self.source_definition["key"]}] Found an iBabs event with status EventUnconfirmed: {str(item.values)}')
        item.status = EventUnconfirmed
    else:
        item.status = EventConfirmed

    item.organization = TopLevelOrganization(self.source_definition['allmanak_id'],
                                             source=self.source_definition['key'],
                                             supplier='allmanak',
                                             collection=self.source_definition['source_type'])

    # Check if this is a committee meeting and if so connect it to the committee node.
    committee_designator = self.source_definition.get('committee_designator', 'commissie')
    if committee_designator in meeting['Meetingtype'].lower():
        # Attach the meeting to the committee node
        item.committee = Organization(meeting['MeetingtypeId'],
                                      source=self.source_definition['key'],
                                      supplier='ibabs',
                                      collection='committee')
        item.committee.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                    source=self.source_definition['key'],
                                                                    supplier='allmanak',
                                                                    collection=self.source_definition['source_type'])

        item.committee.name = meeting['Meetingtype']
        if 'sub' in meeting['MeetingtypeId']:
            item.committee.classification = 'Subcommittee'
        else:
            item.committee.classification = 'Committee'

        # Re-attach the committee node to the municipality node
        item.committee.subOrganizationOf = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                source=self.source_definition['key'],
                                                                supplier='allmanak',
                                                                collection=self.source_definition['source_type'])

    item.agenda = list()
    if meeting['MeetingItems'] and 'iBabsMeetingItem' in meeting['MeetingItems']:
        for i, mi in enumerate(meeting['MeetingItems']['iBabsMeetingItem'] or [], start=1):
            agenda_item = AgendaItem(mi['Id'],
                                     source=self.source_definition['key'],
                                     supplier='ibabs',
                                     collection='agenda_item')
            agenda_item.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                     source=self.source_definition['key'],
                                                                     supplier='allmanak',
                                                                     collection=self.source_definition['source_type'])

            agenda_item.parent = item
            agenda_item.name = mi['Title']
            agenda_item.description = mi['Explanation']
            agenda_item.position, agenda_item.raw_position = translate_position(mi['Features'])
            agenda_item.start_date = item.start_date
            agenda_item.last_discussed_at = item.start_date

            if mi['Documents'] and 'iBabsDocument' in mi['Documents']:
                agenda_item.attachment = list()
                for document in mi['Documents']['iBabsDocument'] or []:
                    attachment = MediaObject(document['Id'],
                                             source=self.source_definition['key'],
                                             supplier='ibabs',
                                             collection='attachment')
                    attachment.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                            source=self.source_definition['key'],
                                                                            supplier='allmanak',
                                                                            collection=self.source_definition['source_type'])

                    attachment.identifier_url = 'ibabs/agenda_item/%s' % document['Id']
                    attachment.original_url = document['PublicDownloadURL']
                    attachment.size_in_bytes = document['FileSize'] or 0
                    attachment.name = document['DisplayName']
                    attachment.file_name = document['FileName']
                    attachment.is_referenced_by = agenda_item
                    attachment.last_discussed_at = item.start_date
                    agenda_item.attachment.append(attachment)

                item.agenda.append(agenda_item)

    item.invitee = list()
    if meeting['Invitees'] and 'iBabsUserBasic' in meeting['Invitees']:
        for invitee in meeting['Invitees']['iBabsUserBasic'] or []:
            invitee_item = Person(invitee['UniqueId'],
                                  source=self.source_definition['key'],
                                  supplier='ibabs',
                                  collection='person')
            invitee_item.name = invitee['Name']
            invitee_item.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                      source=self.source_definition['key'],
                                                                      supplier='allmanak',
                                                                      collection=self.source_definition['source_type'])
            item.invitee.append(invitee_item)

    item.attendee = list()
    if meeting['Attendees'] and 'iBabsUserBasic' in meeting['Attendees']:
        for attendee in meeting['Attendees']['iBabsUserBasic'] or []:
            attendee_item = Person(attendee['UniqueId'],
                                   source=self.source_definition['key'],
                                   supplier='ibabs',
                                   collection='person')
            attendee_item.name = attendee['Name']
            attendee_item.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                       source=self.source_definition['key'],
                                                                       supplier='allmanak',
                                                                       collection=self.source_definition['source_type'])
            item.attendee.append(attendee_item)

    # Double check because sometimes 'EndTime' is in meeting but it is set to None
    if 'EndTime' in meeting and meeting['EndTime']:
        meeting_date, _, _ = meeting['MeetingDate'].partition('T')
        meeting_datetime = '%sT%s:00' % (meeting_date, meeting['EndTime'])
        item.end_date = iso8601.parse_date(meeting_datetime).strftime("%s")
    else:
        item.end_date = iso8601.parse_date(meeting['MeetingDate']).strftime("%s")

    item.attachment = list()
    if meeting['Documents'] and 'iBabsDocument' in meeting['Documents']:
        for document in meeting['Documents']['iBabsDocument'] or []:
            attachment = MediaObject(document['Id'],
                                     source=self.source_definition['key'],
                                     supplier='ibabs',
                                     collection='attachment')
            attachment.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                    source=self.source_definition['key'],
                                                                    supplier='allmanak',
                                                                    collection=self.source_definition['source_type'])

            attachment.identifier_url = 'ibabs/meeting/%s' % document['Id']
            attachment.original_url = document['PublicDownloadURL']
            attachment.size_in_bytes = document['FileSize'] or 0
            attachment.name = document['DisplayName']
            attachment.file_name = document['FileName']
            attachment.is_referenced_by = item
            attachment.last_discussed_at = item.start_date
            item.attachment.append(attachment)

    item.save()
    return item
