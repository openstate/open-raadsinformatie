from datetime import datetime
import json
from pprint import pprint
from hashlib import sha1
from time import sleep
import re

import iso8601

from ocd_backend.items.popolo import MotionItem
from ocd_backend.utils.misc import slugify
from ocd_backend import settings
from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.utils.api import FrontendAPIMixin
from ocd_backend.utils.pdf import PDFToTextMixin


class IBabsMotionItem(
        MotionItem, HttpRequestMixin, FrontendAPIMixin, PDFToTextMixin):
    def _get_council(self):
        """
        Gets the organisation that represents the council.
        """

        results = self.api_request(
            self.source_definition['index_name'], 'organizations',
            classification='Council')
        return results[0]

    def _get_council_members(self):
        results = self.api_request(self.source_definition['index_name'],
            'persons', size=100)  # 100 for now ...
        return results

    def _get_council_parties(self):
        results = self.api_request(self.source_definition['index_name'],
            'organizations', classification='Party', size=100)  # 100 for now ...
        return results

    def _value(self, key):
        return self.original_item['_Extra']['Values'][key]

    def _get_creator(self, creators_str, members, parties):
        # FIXME: currently only does the first. what do we do with the others?
        creator_str = creators_str.split('), ')[0]
        print "Looking for : %s" % (creator_str,)

        party_match = re.search(r' \(([^\)]*?)$', creator_str)
        if not party_match:
            return


        try:
            party = [p for p in parties if p.get('name', u'') == party_match.group(1)][0]
        except Exception as e:
            party = None

        if not party:
            return

        print "Found party: %s" % (party['name'])

        last_name_match = re.match(r'^([^\,]*)\, ', creator_str)
        if not last_name_match:
            return

        last_name_members = [m for m in members if last_name_match.group(1) in m['name']]
        if len(last_name_members) <= 0:
            return

        print "Found last name candidates: %s" % (u','.join([m['name'] for m in last_name_members]),)

        if len(last_name_members) == 1:
            print "Found final candidate base on last name: %s" % (last_name_members[0]['name'],)
            return last_name_members[0]

        for m in last_name_members:
            correct_party_affiliations = [ms for ms in m['memberships'] if ms['organization_id'] == party['id']]
            if len(correct_party_affiliations) > 0:
                print "Found final candidate base on last name and party: %s" % (m['name'],)
                return m

        return None

    def get_original_object_id(self):
        return unicode(self._value('Kenmerk'))

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
        members = self._get_council_members()
        parties = self._get_council_parties()

        meeting = self.original_item
        if self.original_item.has_key('MeetingId'):
            meeting = self.original_item['Meeting']

        combined_index_data['id'] = unicode(self.get_original_object_id())

        combined_index_data['hidden'] = self.source_definition['hidden']

        combined_index_data['name'] = unicode(self._value('Onderwerp'))

        combined_index_data['identifier'] = combined_index_data['id']

        combined_index_data['organization_id'] = council['id']
        combined_index_data['organization'] = council

        creator = self._get_creator(self._value('Indiener(s)'), members, parties)
        if creator is not None:
            combined_index_data['creator_id'] = creator['id']
            combined_index_data['creator'] = creator

        combined_index_data['classification'] = u'Motie'

        # FIXME: put the correct thing in here once this info is sent along ...
        combined_index_data['text'] = self._value('Onderwerp')

        combined_index_data['date'] = iso8601.parse_date(self.original_item['datum'][0],)

        combined_index_data['result'] = self._value('Status')
        combined_index_data['requirement'] = u'majority'
        combined_index_data['sources'] = []

        # FIXME: something with vote events here ...
        combined_index_data['vote_events'] = []

        try:
            documents = self.original_item['Documents']
        except KeyError as e:
            documents = []
        if documents is None:
            documents = []

        for document in documents:
            sleep(1)
            print u"%s: %s" % (
                combined_index_data['name'], document['DisplayName'],)
            description = self.pdf_get_contents(
                document['PublicDownloadURL'],
                self.source_definition.get('pdf_max_pages', 20))
            combined_index_data['sources'].append({
                'url': document['PublicDownloadURL'],
                'note': document['DisplayName'],
                'description': description
            })

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
