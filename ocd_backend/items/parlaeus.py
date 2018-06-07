from datetime import datetime
from hashlib import sha1
from ocd_backend.items.popolo import EventItem, OrganisationItem, PersonItem
from ocd_backend.extractors import HttpRequestMixin


class Meeting(EventItem, HttpRequestMixin):

    @staticmethod
    def get_meeting_id(identifier):
        hash_content = u'meeting-%s' % identifier
        return unicode(sha1(hash_content.decode('utf8')).hexdigest())

    def get_object_id(self):
        return self.get_meeting_id(self.original_item['agid'])

    def get_original_object_id(self):
        return unicode(self.original_item['agid'])

    def get_original_object_urls(self):
        return {"json": self.original_item.get('url')}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['id'] = unicode(self.get_object_id())
        combined_index_data['hidden'] = self.source_definition['hidden']

        combined_index_data['name'] = self.original_item.get('title')
        combined_index_data['description'] = self.original_item.get('description')
        combined_index_data['classification'] = u'Agenda'
        combined_index_data['location'] = self.original_item.get('location')

        combined_index_data['identifiers'] = [
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            },
            {
                'identifier': self.original_item['agid'],
                'scheme': u'Parlaeus'
            }
        ]

        combined_index_data['organization_id'] = Committee.get_committee_id(self.original_item['cmid'])

        if self.original_item.get('time'):
            combined_index_data['start_date'] = datetime.strptime(
                '%s %s' % (self.original_item['date'], self.original_item['time']),
                '%Y%m%d %H:%M'
            )

        if self.original_item.get('endtime') and self.original_item['endtime'] != '0':
            combined_index_data['end_date'] = datetime.strptime(
                '%s %s' % (self.original_item['date'], self.original_item['endtime']),
                '%Y%m%d %H:%M'
            )

        combined_index_data['status'] = u'confirmed'

        # In the past they have assigned cancelled items to a committee
        if self.original_item['committeecode'] == 'geannuleerd':
            combined_index_data['status'] = u'cancelled'

        combined_index_data['children'] = [
            MeetingItem.get_meetingitem_id(mi['apid']) for mi in self.original_item['points']
        ]

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []
        return u' '.join(text_items)


class MeetingItem(EventItem, HttpRequestMixin):

    @staticmethod
    def get_meetingitem_id(identifier):
        hash_content = u'meetingitem-%s' % identifier
        return unicode(sha1(hash_content.decode('utf8')).hexdigest())

    def get_object_id(self):
        return self.get_meetingitem_id(self.original_item['apid'])

    def get_original_object_id(self):
        return unicode(self.original_item['apid'])

    def get_original_object_urls(self):
        return {"json": self.original_item.get('url')}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_combined_index_data(self):
        combined_index_data = {}

        parent = self.original_item['parent']

        combined_index_data['id'] = unicode(self.get_object_id())
        combined_index_data['hidden'] = self.source_definition['hidden']
        combined_index_data['classification'] = u'Agendapunt'

        combined_index_data['identifiers'] = [
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            },
            {
                'identifier': self.original_item['apid'],
                'scheme': u'Parlaeus'
            }
        ]

        if parent.get('time'):
            combined_index_data['start_date'] = datetime.strptime(
                '%s %s' % (parent['date'], parent['time']),
                '%Y%m%d %H:%M'
            )

        if parent.get('endtime') and parent['endtime'] != '0':
            combined_index_data['end_date'] = datetime.strptime(
                '%s %s' % (parent['date'], parent['endtime']),
                '%Y%m%d %H:%M'
            )

        combined_index_data['parent_id'] = unicode(Meeting.get_meeting_id(parent))
        combined_index_data['name'] = self.original_item['title']

        if self.original_item.get('text'):
            combined_index_data['description'] = self.original_item['text']

        media_urls = []
        for doc in self.original_item.get('documents', []):
            media_urls.append(
                {
                    "url": "/v0/resolve/",
                    "note": doc['title'],
                    "original_url": doc['link']
                }
            )
        if media_urls:
            combined_index_data['media_urls'] = media_urls

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []
        return u' '.join(text_items)


class Committee(OrganisationItem):

    @staticmethod
    def get_committee_id(identifier):
        hash_content = u'committee-%s' % identifier
        return unicode(sha1(hash_content.decode('utf8')).hexdigest())

    def get_object_id(self):
        return self.get_committee_id(self.original_item['cmid'])

    def get_original_object_id(self):
        return unicode(self.original_item['cmid'])

    def get_original_object_urls(self):
        return {"json": self.original_item.get('url')}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['id'] = unicode(self.get_object_id())
        combined_index_data['hidden'] = self.source_definition['hidden']

        combined_index_data['name'] = unicode(self.original_item['committeename'])
        combined_index_data['other_names'] = [unicode(self.original_item['committeecode'])]
        combined_index_data['identifiers'] = [
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            },
            {
                'identifier': self.original_item['cmid'],
                'scheme': u'Parlaeus'
            }
        ]
        combined_index_data['classification'] = u'committee'

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []
        return u' '.join(text_items)


class Person(PersonItem):

    @staticmethod
    def get_person_id(identifier):
        hash_content = u'person-%s' % identifier
        return unicode(sha1(hash_content.decode('utf8')).hexdigest())

    def get_object_id(self):
        return self.get_person_id(self.original_item['raid'])

    def get_original_object_id(self):
        return unicode(self.original_item['raid'])

    def get_original_object_urls(self):
        return {"json": self.original_item.get('url')}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['id'] = unicode(self.get_object_id())
        combined_index_data['hidden'] = self.source_definition['hidden']

        combined_index_data['name'] = unicode(self.original_item['name'])
        combined_index_data['identifiers'] = [
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            },
            {
                'identifier': self.original_item['raid'],
                'scheme': u'Parlaeus'
            }
        ]

        combined_index_data['memberships'] = [
            {
                'label': unicode(self.original_item['function']),
                'role': unicode(self.original_item['function']),
                'person_id': unicode(self.get_object_id()),
                #'organization': unicode(self.original_item['party']),
            }
        ]

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []
        return u' '.join(text_items)
