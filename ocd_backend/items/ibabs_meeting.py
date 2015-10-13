from datetime import datetime
import json
from pprint import pprint
from hashlib import sha1
from time import sleep

import iso8601

from ocd_backend.items.popolo import EventItem
from ocd_backend.utils.misc import slugify
from ocd_backend import settings
from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.utils.api import FrontendAPIMixin
from ocd_backend.utils.pdf import PDFToTextMixin


class IBabsMeetingItem(
        EventItem, HttpRequestMixin, FrontendAPIMixin, PDFToTextMixin):
    def _get_council(self):
        """
        Gets the organisation that represents the council.
        """

        results = self.api_request(
            self.source_definition['index_name'], 'organizations',
            classification='council')
        return results[0]

    def _find_meeting_type_id(self, org):
        results = [x for x in org['identifiers'] if x['scheme'] == u'iBabs']
        return results[0]['identifier']

    def _get_committees(self):
        """
        Gets the committees that are active for the council.
        """

        results = self.api_request(
            self.source_definition['index_name'], 'organizations',
            classification=['committee', 'subcommittee'])
        return {self._find_meeting_type_id(c): c for c in results}

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

    def get_combined_index_data(self):
        combined_index_data = {}
        council = self._get_council()
        committees = self._get_committees()

        meeting = self.original_item
        if self.original_item.has_key('MeetingId'):
            meeting = self.original_item['Meeting']

        combined_index_data['id'] = unicode(self.get_object_id())

        combined_index_data['hidden'] = self.source_definition['hidden']

        if self.original_item.has_key('Title'):
            combined_index_data['name'] = u'%s: %s' % (
                unicode(self.original_item['Features']),
                unicode(self.original_item['Title']),)
        else:
            combined_index_data['name'] = self.get_collection()

        combined_index_data['identifiers'] = [
            {
                'identifier': unicode(self.original_item['Id']),
                'scheme': u'iBabs'
            },
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            }
        ]

        try:
            combined_index_data['organization_id'] = committees[
                meeting['MeetingtypeId']]['id']
            combined_index_data['organization'] = committees[
                meeting['MeetingtypeId']]
        except KeyError as e:
            combined_index_data['organization_id'] = council['id']
            combined_index_data['organization'] = council

        combined_index_data['classification'] = (
            u'Meeting Item' if self.original_item.has_key('MeetingId') else
            u'Meeting')
        combined_index_data['description'] = self.original_item['Explanation']
        combined_index_data['start_date'] = iso8601.parse_date(
            meeting['MeetingDate'],)
        combined_index_data['end_date'] = iso8601.parse_date(
            meeting['MeetingDate'],)
        combined_index_data['location'] = meeting['Location'].strip()
        combined_index_data['status'] = u'confirmed'

        if self.original_item.has_key('MeetingId'):
            combined_index_data['parent_id'] = unicode(self._get_meeting_id(
                meeting))

        if self.original_item.has_key('MeetingItems'):
            combined_index_data['children'] = [
                self._get_meeting_id(mi) for mi in self.original_item[
                    'MeetingItems']]

        combined_index_data['sources'] = []

        try:
            documents = self.original_item['Documents']
        except KeyError as e:
            documents = []
        if documents is None:
            documents = []

        for document in documents:
            # sleep(1)
            print u"%s: %s" % (
                combined_index_data['name'], document['DisplayName'],)
            combined_index_data['sources'].append({
                'url': document['PublicDownloadURL'],
                'note': document['DisplayName'],
                # FIXME: some attachments are huuuuuge (>1,000 pages)
                # TODO: what to do about those?
                # FIXME: we should have resolver URLs for these ...
                #'description': self.pdf_get_contents(
                #    document['PublicDownloadURL'])
            })

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)


class IBabsReportItem(
        EventItem, HttpRequestMixin, FrontendAPIMixin, PDFToTextMixin):
    def _get_council(self):
        """
        Gets the organisation that represents the council.
        """

        results = self.api_request(
            self.source_definition['index_name'], 'organizations',
            classification='council')
        return results[0]

    def _get_committees(self):
        """
        Gets the committees that are active for the council.
        """

        results = self.api_request(
            self.source_definition['index_name'], 'organizations',
            classification=['committee', 'subcommittee'])
        return {c['name']: c for c in results}

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
        return u'%s' % (self.original_item['_ReportName'])

    def get_combined_index_data(self):
        combined_index_data = {}
        council = self._get_council()
        committees = self._get_committees()

        combined_index_data['id'] = unicode(self.get_object_id())

        combined_index_data['hidden'] = self.source_definition['hidden']

        name_field = None
        for field in self.original_item.keys():
            id_for_field = '%sIds' % (field,)
            if (
                self.original_item.has_key(id_for_field) and
                name_field is None
            ):
                name_field = field

        combined_index_data['name'] = unicode(
            self.original_item[name_field][0])

        combined_index_data['identifiers'] = [
            {
                'identifier': unicode(self.original_item['id'][0]),
                'scheme': u'iBabs'
            },
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            }
        ]

        combined_index_data['organization_id'] = council['id']
        combined_index_data['organization'] = council
        found_committee = False
        for comm_name, comm in committees.iteritems():
            if (
                comm_name.lower() in combined_index_data['name'].lower() and
                not found_committee
            ):
                combined_index_data['organization_id'] = comm['id']
                combined_index_data['organization'] = comm
                found_committee = True

        report_name = unicode(
            self.original_item['_ReportName'].split(r'\s+')[0])

        if u'Besluitenlijsten' in report_name:
            combined_index_data['classification'] = u'Resolution'
        else:
            combined_index_data['classification'] = u'Report'

        combined_index_data['description'] = combined_index_data['name']

        # FIXME: maybe datum should not be hardcoded?
        if self.original_item.has_key('datum'):
            combined_index_data['start_date'] = iso8601.parse_date(
                self.original_item['datum'][0],)
            combined_index_data['end_date'] = iso8601.parse_date(
                self.original_item['datum'][0],)
        # combined_index_data['location'] = meeting['Location'].strip()
        combined_index_data['status'] = u'confirmed'

        combined_index_data['sources'] = []
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
                    'description': self.pdf_get_contents(
                        self._get_public_url(b),
                        self.source_definition.get('pdf_max_pages', 20)),
                }, field_values, field_ids)
            combined_index_data['sources'] += documents

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
