import re

import iso8601

from ocd_backend import celery_app
from ocd_backend.transformers import BaseTransformer
from ocd_backend.models import *
from ocd_backend.log import get_source_logger

log = get_source_logger('ibabs_meeting')


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=(Exception,), retry_backoff=True)
def meeting_item(self, content_type, raw_item, entity, source_item, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'ibabs',
        'collection': 'meeting',
    }

    # Sometimes the meeting is contained in a sub-dictionary called 'Meeting'
    if 'Meeting' in original_item:
        meeting = original_item['Meeting']
    else:
        meeting = original_item

    item = Meeting(meeting['Id'], **source_defaults)
    item.canonical_id = entity
    item.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                      source=self.source_definition['key'],
                                                      supplier='allmanak',
                                                      collection=self.source_definition['source_type'])

    item.name = meeting['Meetingtype']
    item.chair = meeting['Chairman']
    item.location = meeting['Location']
    item.start_date = iso8601.parse_date(meeting['MeetingDate'], ).strftime("%s")

    # TODO: This is untested so we log any cases that are not the default
    if 'canceled' in meeting and meeting['canceled']:
        log.info('Found an iBabs event with status EventCancelled: %s' % str(item.values))
        item.status = EventCancelled
    elif 'inactive' in meeting and meeting['inactive']:
        log.info('Found an iBabs event with status EventUnconfirmed: %s' % str(item.values))
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
            item.committee.classification = u'Subcommittee'
        else:
            item.committee.classification = u'Committee'

        # Re-attach the committee node to the municipality node
        item.committee.subOrganizationOf = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                source=self.source_definition['key'],
                                                                supplier='allmanak',
                                                                collection=self.source_definition['source_type'])

    item.agenda = list()
    for i, mi in enumerate(meeting['MeetingItems']['iBabsMeetingItem'] or [], start=1):
        agenda_item = AgendaItem(mi['Id'],
                                 source=self.source_definition['key'],
                                 supplier='ibabs',
                                 collection='agenda_item')
        agenda_item.canonical_id = mi['Id']
        agenda_item.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                 source=self.source_definition['key'],
                                                                 supplier='allmanak',
                                                                 collection=self.source_definition['source_type'])

        agenda_item.parent = item
        agenda_item.name = mi['Title']
        agenda_item.start_date = item.start_date

        if mi['Documents'] and 'iBabsDocument' in mi['Documents']:
            agenda_item.attachment = list()
            for document in mi['Documents']['iBabsDocument'] or []:
                attachment = MediaObject(document['Id'],
                                         source=self.source_definition['key'],
                                         supplier='ibabs',
                                         collection='attachment')
                attachment.canonical_id = document['Id']
                attachment.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                        source=self.source_definition['key'],
                                                                        supplier='allmanak',
                                                                        collection=self.source_definition['source_type'])

                attachment.identifier_url = 'ibabs/agenda_item/%s' % document['Id']
                attachment.original_url = document['PublicDownloadURL']
                attachment.size_in_bytes = document['FileSize']
                attachment.name = document['DisplayName']
                attachment.isReferencedBy = agenda_item
                agenda_item.attachment.append(attachment)

            item.agenda.append(agenda_item)

    item.invitee = list()
    for invitee in meeting['Invitees']['iBabsUserBasic'] or []:
        invitee_item = Person(invitee['UniqueId'],
                              source=self.source_definition['key'],
                              supplier='ibabs',
                              collection='person')
        invitee_item.canonical_id = invitee['UniqueId']
        invitee_item.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                  source=self.source_definition['key'],
                                                                  supplier='allmanak',
                                                                  collection=self.source_definition['source_type'])
        item.invitee.append(invitee_item)

    # Double check because sometimes 'EndTime' is in meeting but it is set to None
    if 'EndTime' in meeting and meeting['EndTime']:
        meeting_date, _, _ = meeting['MeetingDate'].partition('T')
        meeting_datetime = '%sT%s:00' % (meeting_date, meeting['EndTime'])
        item.end_date = iso8601.parse_date(meeting_datetime).strftime("%s")
    else:
        item.end_date = iso8601.parse_date(meeting['MeetingDate'], ).strftime("%s")

    item.attachment = list()
    for document in meeting['Documents']['iBabsDocument'] or []:
        attachment = MediaObject(document['Id'],
                                 source=self.source_definition['key'],
                                 supplier='ibabs',
                                 collection='attachment')
        attachment.canonical_id = document['Id']
        attachment.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                source=self.source_definition['key'],
                                                                supplier='allmanak',
                                                                collection=self.source_definition['source_type'])

        attachment.identifier_url = 'ibabs/meeting/%s' % document['Id']
        attachment.original_url = document['PublicDownloadURL']
        attachment.size_in_bytes = document['FileSize']
        attachment.name = document['DisplayName']
        attachment.isReferencedBy = item
        item.attachment.append(attachment)

    item.save()
    return item


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=(Exception,), retry_backoff=True)
def report_item(self, content_type, raw_item, entity, source_item, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    source_defaults = {
        'source': self.source_definition['key'],
        'supplier': 'ibabs',
        'collection': 'report',
    }

    report = CreativeWork(original_item['id'][0],
                          source=self.source_definition['key'],
                          supplier='ibabs',
                          collection='report')
    report.canonical_id = original_item['id'][0]
    report.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                        source=self.source_definition['key'],
                                                        supplier='allmanak',
                                                        collection=self.source_definition['source_type'])

    report_name = original_item['_ReportName'].split(r'\s+')[0]
    report.classification = u'Report'

    name_field = None
    try:
        name_field = self.source_definition['fields'][report_name]['name']
    except KeyError:
        for field in original_item.keys():
            # Search for things that look like title
            if field.lower()[0:3] == 'tit':
                name_field = field
                break

            id_for_field = '%sIds' % (field,)
            if id_for_field in original_item and name_field is None:
                name_field = field
                break

    report.name = original_item[name_field][0]

    # Temporary binding reports to municipality as long as events and agendaitems are not
    # referenced in the iBabs API
    report.creator = TopLevelOrganization(self.source_definition['allmanak_id'],
                                          source=self.source_definition['key'],
                                          supplier='allmanak',
                                          collection=self.source_definition['source_type'])

    try:
        name_field = self.source_definition['fields'][report_name]['description']
        report.description = original_item[name_field][0]
    except KeyError:
        try:
            report.description = original_item['_Extra']['Values']['Toelichting']
        except KeyError:
            pass

    try:
        datum_field = self.source_definition['fields'][report_name]['start_date']
    except KeyError:
        datum_field = 'datum'

    datum = None
    if datum_field in original_item:
        if isinstance(original_item[datum_field], list):
            datum = original_item[datum_field][0]
        else:
            datum = original_item[datum_field]

    if datum is not None:
        # msgpack does not like microseconds for some reason.
        # no biggie if we disregard it, though
        report.start_date = iso8601.parse_date(re.sub(r'\.\d+\+', '+', datum))
        report.end_date = iso8601.parse_date(re.sub(r'\.\d+\+', '+', datum))

    report.status = EventConfirmed

    report.attachment = list()
    for document in original_item['_Extra']['Documents'] or []:
        attachment_file = MediaObject(document['Id'],
                                      source=self.source_definition['key'],
                                      supplier='ibabs',
                                      collection='attachment')
        attachment_file.canonical_id = document['Id']
        attachment_file.has_organization_name = TopLevelOrganization(self.source_definition['allmanak_id'],
                                                                     source=self.source_definition['key'],
                                                                     supplier='allmanak',
                                                                     collection=self.source_definition['source_type'])

        attachment_file.original_url = document['PublicDownloadURL']
        attachment_file.size_in_bytes = document['FileSize']
        attachment_file.name = document['DisplayName']
        attachment_file.isReferencedBy = report
        report.attachment.append(attachment_file)

    report.save()
    return report
