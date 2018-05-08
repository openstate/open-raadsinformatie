from hashlib import sha1

from ocd_backend.items.notubiz_meeting import Meeting
from ocd_backend.models import *


def get_meetingitem_id(item_id):
    hash_content = u'meetingitem-%s' % item_id
    return unicode(sha1(hash_content.decode('utf8')).hexdigest())


class MeetingItem(Meeting):
    @staticmethod
    def _get_meeting_id(item_id):
        from ocd_backend.items.notubiz_meeting import get_meeting_id
        return get_meeting_id(item_id)

    def get_object_id(self):
        return get_meetingitem_id(self.original_item['id'])

    def _get_current_permalink(self):
        return u'%s/agenda_items/agenda_points/%i' % (self.source_definition['base_url'], self.original_item['id'])

    def get_object_model(self):
        agenda_item = AgendaItem('notubiz_identifier', self.original_item['id'])

        try:
            parent_id = self.original_item['parent']['id']
        except TypeError:
            parent_id = self.original_item['meeting']['id']
        agenda_item.parent = Event.get_or_create(notubiz_identifier=parent_id)

        agenda_item.agenda = []
        for item in self.original_item.get('agenda_items', []):
            agendaitem = AgendaItem.get_or_create(notubiz_identifier=item['id'])
            agenda_item.__rel_params__ = {'rdf': '_%i' % item['order']}
            agenda_item.agenda.append(agendaitem)

        agenda_item.attachment = []
        for doc in self.original_item.get('documents', []):
            attachment = Attachment('notubiz_identifier', doc['id'])
            attachment.original_url = doc['url']
            attachment.name = doc['title']
            agenda_item.attachment.append(attachment)

        # If it's a 'label' type some attributes do not exist
        if self.original_item['type'] == 'label':
            agenda_item.name = self.original_item['type_data']['title']
            return agenda_item

        agenda_item.name = self.original_item['attributes']['Titel']
        agenda_item.position = self.original_item['order']

        return agenda_item

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
