import re

import iso8601

from ocd_backend.items import BaseItem
from ocd_backend.log import get_source_logger
from ocd_backend.models import *

log = get_source_logger('ibabs_meeting')


class IBabsMeetingItem(BaseItem):
    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        source_defaults = {
            'source': 'ibabs',
            'source_id_key': 'identifier',
            'organization': self.source_definition['index_name'],
        }

        # Sometimes the meeting is contained in a sub-dictionary called 'Meeting'
        if 'Meeting' in self.original_item:
            meeting = self.original_item['Meeting']
        else:
            meeting = self.original_item

        item = Meeting(meeting['Id'], **source_defaults)
        item.name = meeting['Meetingtype']
        item.chair = meeting['Chairman']
        item.location = meeting['Location']
        item.start_date = iso8601.parse_date(meeting['MeetingDate'], ).strftime("%s")

        # TODO: This is untested so we log any cases that are not the default
        if 'canceled' in meeting and meeting['canceled']:
            log.info('Found an iBabs event with status EventCancelled: %s' % str(item.values))
            item.status = EventCancelled()
        elif 'inactive' in meeting and meeting['inactive']:
            log.info('Found an iBabs event with status EventUnconfirmed: %s' % str(item.values))
            item.status = EventUnconfirmed()
        else:
            item.status = EventConfirmed()

        # Attach the meeting to the municipality node
        item.organization = Organization(self.source_definition['key'], **source_defaults)
        item.organization.merge(collection=self.source_definition['key'])

        # Check if this is a committee meeting and if so connect it to the committee node. If it is
        # not a committee meeting we attach it to the 'Gemeenteraad' committee node
        committee_designator = self.source_definition.get('committee_designator', 'commissie')
        if committee_designator in meeting['Meetingtype'].lower():
            # Attach the meeting to the committee node
            item.committee = Organization(meeting['MeetingtypeId'], **source_defaults)
            item.committee.name = meeting['Meetingtype']
            if 'sub' in meeting['MeetingtypeId']:
                item.committee.classification = u'Subcommittee'
            else:
                item.committee.classification = u'Committee'
            # Re-attach the committee node to the municipality node
            # TODO: Why does the committee node get detached from the municipality node when meetings are attached to it?
            item.committee.parent = Organization(self.source_definition['key'], **source_defaults)
            item.committee.parent.merge(collection=self.source_definition['key'])
        else:
            # This is not a committee meeting, so attach it to the 'Gemeenteraad' committee node
            item.committee = Organization('gemeenteraad', **source_defaults)
            item.committee.name = 'Gemeenteraad'
            item.committee.classification = 'Council'
            item.committee.collection = self.source_definition['key'] + '-gemeenteraad'
            item.committee.merge(collection=self.source_definition['key'] + '-gemeenteraad')
            # Re-attach the 'Gemeenteraad' committee node to the municipality node
            # TODO: Same problem as above
            item.committee.parent = Organization(self.source_definition['key'], **source_defaults)
            item.committee.parent.merge(collection=self.source_definition['key'])

        if 'MeetingItems' in meeting:
            item.agenda = list()
            for i, mi in enumerate(meeting['MeetingItems'] or [], start=1):
                agenda_item = AgendaItem(mi['Id'], **source_defaults)
                agenda_item.parent = item
                agenda_item.name = mi['Title']
                agenda_item.start_date = item.start_date
                agenda_item.__rel_params__ = {'rdf': '_%i' % i}
                item.agenda.append(agenda_item)

        item.invitee = list()
        for invitee in meeting['Invitees'] or []:
            item.invitee.append(Person(invitee['UniqueId'],
                                       **source_defaults))

        # Double check because sometimes 'EndTime' is in meeting but it is set to None
        if 'EndTime' in meeting and meeting['EndTime']:
            meeting_date, _, _ = meeting['MeetingDate'].partition('T')
            meeting_datetime = '%sT%s:00' % (meeting_date, meeting['EndTime'])
            item.end_date = iso8601.parse_date(meeting_datetime).strftime("%s")
        else:
            item.end_date = iso8601.parse_date(meeting['MeetingDate'], ).strftime("%s")

        item.attachment = list()
        for document in meeting['Documents'] or []:
            attachment = MediaObject(document['Id'], **source_defaults)
            attachment.original_url = document['PublicDownloadURL']
            attachment.size_in_bytes = document['FileSize']
            attachment.name = document['DisplayName']
            item.attachment.append(attachment)

        return item


class IBabsReportItem(BaseItem):

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        source_defaults = {
            'source': 'ibabs',
            'source_id_key': 'identifier',
            'organization': self.source_definition['index_name'],
        }

        report = CreativeWork(self.original_item['id'][0], **source_defaults)  # todo

        report_name = self.original_item['_ReportName'].split(r'\s+')[0]
        report.classification = u'Report'

        name_field = None
        try:
            name_field = self.source_definition['fields'][report_name]['name']
        except KeyError:
            for field in self.original_item.keys():
                # Search for things that look like title
                if field.lower()[0:3] == 'tit':
                    name_field = field
                    break

                id_for_field = '%sIds' % (field,)
                if id_for_field in self.original_item and name_field is None:
                    name_field = field
                    break

        report.name = self.original_item[name_field][0]

        # Temporary binding reports to municipality as long as events and agendaitems are not
        # referenced in the iBabs API
        report.creator = Organization(self.source_definition['key'], **source_defaults)
        report.creator.merge(collection=self.source_definition['key'])

        try:
            name_field = self.source_definition['fields'][report_name]['description']
            report.description = self.original_item[name_field][0]
        except KeyError:
            try:
                report.description = self.original_item['_Extra']['Values']['Toelichting']
            except KeyError:
                pass

        try:
            datum_field = self.source_definition['fields'][report_name]['start_date']
        except KeyError:
            datum_field = 'datum'

        datum = None
        if datum_field in self.original_item:
            if isinstance(self.original_item[datum_field], list):
                datum = self.original_item[datum_field][0]
            else:
                datum = self.original_item[datum_field]

        if datum is not None:
            # msgpack does not like microseconds for some reason.
            # no biggie if we disregard it, though
            report.start_date = iso8601.parse_date(re.sub(r'\.\d+\+', '+', datum))
            report.end_date = iso8601.parse_date(re.sub(r'\.\d+\+', '+', datum))

        report.status = EventConfirmed()

        report.attachment = list()
        for document in self.original_item['_Extra']['Documents'] or []:
            attachment_file = MediaObject(document['Id'], **source_defaults)
            attachment_file.original_url = document['PublicDownloadURL']
            attachment_file.size_in_bytes = document['FileSize']
            attachment_file.name = document['DisplayName']
            report.attachment.append(attachment_file)

        return report
