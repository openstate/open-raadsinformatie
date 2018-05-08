import re
from hashlib import sha1
from time import sleep

import iso8601

from ocd_backend import settings
from ocd_backend.items import BaseItem
from ocd_backend.models import *
from ocd_backend.log import get_source_logger

log = get_source_logger('item')


class IBabsMeetingItem(BaseItem):
    def _find_meeting_type_id(self, org):
        results = [x for x in org['identifiers'] if x['scheme'] == u'iBabs']
        return results[0]['identifier']

    def _get_meeting_id(self, meeting):
        hash_content = u'meeting-%s' % (meeting['Id'])
        return sha1(hash_content.decode('utf8')).hexdigest()

    def get_object_id(self):
        return self._get_meeting_id(self.original_item)

    def get_original_object_id(self):
        return unicode(self.original_item['Id']).strip()

    def get_original_object_urls(self):
        # FIXME: what to do when there is not an original URL?
        return {"html": settings.IBABS_WSDL}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        #council = self._get_council()
        #committees = self._get_committees()

        meeting = self.original_item
        if 'MeetingId' not in self.original_item:
            item = Event('ibabs_identifier', self.original_item['Id'])
            item.name = meeting['Meetingtype']
            item.chair = meeting['Chairman']
            item.location = meeting['Location'].strip()
            organization = Organization.get_or_create(attribute='MeetingtypeId')
            organization.value = meeting['MeetingtypeId']
            item.organization = organization

            if 'MeetingItems' in meeting:
                item.agenda = list()
                for i, mi in enumerate(meeting['MeetingItems'] or [], start=1):
                    agenda_item = AgendaItem.get_or_create(ibabs_identifier=mi['Id'])
                    agenda_item.__rel_params__ = {'rdf': '_%i' % i}
                    item.agenda.append(agenda_item)

            item.invitee = list()
            for invitee in meeting['Invitees'] or []:
                item.invitee.append(Person.get_or_create(ibabs_identifier=invitee['UniqueId']))
        else:
            meeting = self.original_item['Meeting']
            item = AgendaItem('ibabs_identifier', self.original_item['Id'])
            item.name = u'%s: %s' % (
                self.original_item['Features'],
                self.original_item['Title'],
            )
            item.description = self.original_item['Explanation']

            event = Event.get_or_create(ibabs_identifier=self.original_item['MeetingId'])
            event.attachment = Attachment.get_or_create(ibabs_identifier=self.original_item['MeetingId'])
            item.parent = event

        item.start_date = iso8601.parse_date(meeting['MeetingDate'],).strftime("%s")
        item.end_date = iso8601.parse_date(meeting['MeetingDate'],).strftime("%s")

        item.attachment = list()
        for document in self.original_item['Documents'] or []:
            attachment = Attachment('ibabs_identifier', document['Id'])
            attachment.original_url = document['PublicDownloadURL']
            attachment.size_in_bytes = document['FileSize']
            attachment.name = document['DisplayName']
            item.attachment.append(attachment)

        return item

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)


class IBabsReportItem(BaseItem):
    def _get_council(self):
        """
        Gets the organisation that represents the council.
        """

        results = self.api_request(
            self.source_definition['index_name'], 'organizations',
            classification='Council')
        return results[0]

    def _get_committees(self):
        """
        Gets the committees that are active for the council.
        """

        try:
            results = self.api_request(
                self.source_definition['index_name'], 'organizations',
                classification=['committee', 'subcommittee'])
            return {c['name']: c for c in results}
        except TypeError:
            return {}

    def _get_public_url(self, doc_id):
        return (
            u'https://www.mijnbabs.nl/babsapi/publicdownload.aspx?'
            u'site=%s&id=%s' % (self.source_definition['sitename'], doc_id,))

    def get_original_object_id(self):
        return unicode(self.original_item['id'][0]).strip()

    def get_original_object_urls(self):
        # FIXME: what to do when there is not an original URL?
        return {"html": settings.IBABS_WSDL}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        object_model = {}
        council = self._get_council()
        committees = self._get_committees()

        object_model['id'] = unicode(self.get_object_id())

        object_model['hidden'] = self.source_definition['hidden']

        report_name = unicode(
            self.original_item['_ReportName'].split(r'\s+')[0])

        object_model['classification'] = report_name


        name_field = None
        try:
            name_field = self.source_definition['fields'][report_name]['name']
        except KeyError as e:
            for field in self.original_item.keys():
                # Search for things that look like title
                if field.lower()[0:3] == 'tit':
                    name_field = field
                    break

                id_for_field = '%sIds' % (field,)
                if (
                    self.original_item.has_key(id_for_field) and
                    name_field is None
                ):
                    name_field = field
                    break

        object_model['name'] = unicode(
            self.original_item[name_field][0])

        object_model['identifiers'] = [
            {
                'identifier': unicode(self.original_item['id'][0]),
                'scheme': u'iBabs'
            },
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            }
        ]

        object_model['organization_id'] = council['id']
        object_model['organization'] = council
        found_committee = False
        for comm_name, comm in committees.iteritems():
            if (
                comm_name.lower() in object_model['name'].lower() and
                not found_committee
            ):
                object_model['organization_id'] = comm['id']
                object_model['organization'] = comm
                found_committee = True

        try:
            name_field = self.source_definition['fields'][report_name]['description']
            object_model['description'] = unicode(
                self.original_item[name_field][0])
        except KeyError as e:
            object_model['description'] = u''

        if object_model['description'].strip() == u'':
            try:
                object_model['description'] = self.original_item['_Extra']['Values']['Toelichting']
            except KeyError as e:
                object_model['description'] = None

        try:
            datum_field = self.source_definition['fields'][report_name]['start_date']
        except Exception as e:
            datum_field = 'datum'

        datum = None
        if self.original_item.has_key(datum_field):
            if isinstance(self.original_item[datum_field], list):
                datum = self.original_item[datum_field][0]
            else:
                datum = self.original_item[datum_field]

        if datum is not None:
            # msgpack does not like microseconds for some reason.
            # no biggie if we disregard it, though
            object_model['start_date'] = iso8601.parse_date(
                re.sub(r'\.\d+\+', '+', datum),)
            object_model['end_date'] = iso8601.parse_date(
                re.sub(r'\.\d+\+', '+', datum),)

        # object_model['location'] = meeting['Location'].strip()
        object_model['status'] = u'confirmed'

        object_model['sources'] = []

        try:
            documents = self.original_item['_Extra']['Documents']
        except KeyError as e:
            documents = []
        if documents is None:
            documents = []

        for document in documents:
            sleep(1)
            log.debug(u"Extra docs : %s: %s" % (
                object_model['name'], document['DisplayName'],))
            description = self.file_get_contents(
                public_download_url,
                self.source_definition.get('pdf_max_pages', 20))
            object_model['sources'].append({
                'url': document['PublicDownloadURL'],
                'note': document['DisplayName'],
                'description': description
            })

        for field in self.original_item.keys():
            id_for_field = '%sIds' % (field,)
            if not self.original_item.has_key(id_for_field):
                continue
            if (
                self.original_item[field][0] ==
                self.original_item[id_for_field][0]
            ):
                continue
            field_values = self.original_item[field][0].split(r'\s*;\s*')
            field_ids = self.original_item[id_for_field][0].split(r'\s*;\s*')
            documents = map(
                lambda a, b: {
                    'url': self._get_public_url(b),
                    'notes': a,
                    'description': self.file_get_contents(
                        self._get_public_url(b),
                        self.source_definition.get('pdf_max_pages', 20)),
                }, field_values, field_ids)
            object_model['sources'] += documents

        return object_model

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
