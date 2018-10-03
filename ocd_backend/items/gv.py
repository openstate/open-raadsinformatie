from datetime import datetime
import json
from pprint import pprint
import re
from hashlib import sha1
from time import sleep

import iso8601

from ocd_backend.items.popolo import EventItem
from ocd_backend.utils.misc import slugify
from ocd_backend import settings
from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.utils.api import FrontendAPIMixin
from ocd_backend.utils.file_parsing import FileToTextMixin


class GreenValleyItem(
        EventItem, HttpRequestMixin, FrontendAPIMixin):
    def _get_documents_as_media_urls(self):
        media_urls = {}
        for att_key, att in self.original_item.get(u'attachmentlist', {}).iteritems():
            if att[u'objecttype'] == 'AGENDAPAGE':
                continue

            url = "https://staten.zuid-holland.nl/dsresource?objectid=%s" % (
                att[u'objectid'],)

            doc_hash = unicode(sha1(
                (url + u':' + att[u'objectname']).decode(
                    'utf8')).hexdigest())
            media_urls[doc_hash] = {
                "url": "/v0/resolve/",
                "note": att[u'objectname'],
                "original_url": url
            }
        if media_urls:
            return media_urls.values()
        else:
            return None

    def _get_council(self):
        """
        Gets the organisation that represents the council.
        """

        results = self.api_request(
            self.source_definition['index_name'], 'organizations',
            classification='Council')
        try:
            return results[0]
        except TypeError:
            return None

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
        try:
            return {self._find_meeting_type_id(c): c for c in results}
        except TypeError:
            return {}

    def _get_meeting_id(self, meeting):
        hash_content = u'%s-%s' % (
            meeting[u'objecttype'],
            meeting[u'objectid'])
        return sha1(hash_content.decode('utf8')).hexdigest()

    def get_object_id(self):
        return self._get_meeting_id(self.original_item[u'default'])

    def get_original_object_id(self):
        return unicode(
            self.original_item[u'default'][u'objectid']).strip()

    def get_original_object_urls(self):
        # FIXME: what to do when there is not an original URL?
        return {}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_combined_index_data(self):
        objecttype2classification = {
            'agenda': 'Agenda',
            'agendapage': 'Agendapunt',
            'bestuurlijkstuk': 'Bestuurlijk stuk',
            'notule': 'Verslag',
            'ingekomenstuk': 'Ingekomen stuk',
            'antwoordstuk': 'Antwoord'  # ?
        }

        council = self._get_council()
        committees = self._get_committees()

        combined_index_data = {}

        meeting = self.original_item[u'default']

        combined_index_data['id'] = unicode(self.get_object_id())

        combined_index_data['hidden'] = self.source_definition['hidden']

        combined_index_data['name'] = meeting[u'objectname']

        combined_index_data['identifiers'] = [
            {
                'identifier': unicode(meeting[u'objectid']),
                'scheme': u'GreenValley'
            },
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            }
        ]

        try:
            combined_index_data['classification'] = unicode(
                objecttype2classification[meeting[u'objecttype'].lower()])
        except LookupError:
            combined_index_data['classification'] = unicode(
            meeting[u'objecttype'].capitalize())
        combined_index_data['description'] = meeting[u'objectname']

        if council is not None:
            combined_index_data['organization_id'] = council['id']
            combined_index_data['organization'] = council
        combined_index_data['status'] = u'confirmed'

        if meeting.get(u'bis_vergaderdatum', u'').strip() != u'':
            combined_index_data['start_date'] = datetime.fromtimestamp(
                float(meeting[u'bis_vergaderdatum']) +
                (float(meeting.get(u'bis_starttijduren', '0') or '0') * 3600) +
                (float(meeting.get(u'bis_starttijdminuten', '0') or '0') * 60))
            combined_index_data['end_date'] = datetime.fromtimestamp(
                float(meeting[u'bis_vergaderdatum']) +
                (float(meeting.get(u'bis_eindtijduren', '0') or '0') * 3600) +
                (float(meeting.get(u'bis_eindtijdminuten', '0') or '0') * 60))
        elif u'publishdate' in meeting:
            combined_index_data['start_date'] = datetime.fromtimestamp(
                float(meeting[u'publishdate']))
            combined_index_data['end_date'] = datetime.fromtimestamp(
                float(meeting[u'publishdate']))
        try:
            combined_index_data['location'] = meeting[u'bis_locatie'].strip()
        except (AttributeError, KeyError):
            pass

        children = []
        for a, v in self.original_item.get(u'SETS', {}).iteritems():
            if v[u'objecttype'].lower() == u'agendapage':
                result = {u'default': v}
                children.append(result)

        if len(children) > 0:
            try:
                combined_index_data['children'] = [
                    self._get_meeting_id(y) for y in sorted(
                        children, key=lambda x: x[u'default'][u'nodeorder'])]
            except Exception as e:
                pass
                # print str(children)

        if u'parent_objectid' in meeting:
            combined_index_data['parent_id'] = unicode(self._get_meeting_id(
                {
                    u'objectid': meeting[u'parent_objectid'],
                    u'objecttype': 'AGENDA'}))

        combined_index_data['sources'] = []
        print "Document has %s attachments" % (
            len(self.original_item.get(u'attachmentlist', {}),))
        # for att_key, att in self.original_item.get(u'attachmentlist', {}).iteritems():
        #     if att[u'objecttype'] == 'AGENDAPAGE':
        #         continue
        #
        #     url = "https://staten.zuid-holland.nl/dsresource?objectid=%s" % (
        #         att[u'objectid'],)
        #
        #     description = self.file_get_contents(
        #         url,
        #         self.source_definition.get('pdf_max_pages', 20)
        #     )
        #
        #     combined_index_data['sources'].append({
        #         'url': url,
        #         'note': att[u'objectname'],
        #         'description': description
        #     })

        combined_index_data['media_urls'] = self._get_documents_as_media_urls()

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)


class GreenValleyMeetingItem(GreenValleyItem):
    def get_combined_index_data(self):
        combined_index_data = super(
            GreenValleyMeetingItem, self).get_combined_index_data()

        council = self._get_council()
        committees = self._get_committees()

        if council is not None:
            combined_index_data['organization_id'] = council['id']
            combined_index_data['organization'] = council
        combined_index_data['status'] = u'confirmed'

        return combined_index_data
