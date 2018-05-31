from ocd_backend.items.notubiz_meeting import NotubizMeeting
from ocd_backend.models import *


class NotubizMeetingItem(NotubizMeeting):
    def get_object_model(self):
        agenda_item = AgendaItem('notubiz_identifier', self.original_item['id'])

        try:
            parent_id = self.original_item['parent']['id']
        except TypeError:
            parent_id = self.original_item['meeting']['id']
        agenda_item.parent = Meeting.get_or_create(notubiz_identifier=parent_id)

        agenda_item.agenda = []
        for item in self.original_item.get('agenda_items', []):
            agendaitem = AgendaItem.get_or_create(notubiz_identifier=item['id'])
            agenda_item.__rel_params__ = {'rdf': '_%i' % item['order']}
            agenda_item.agenda.append(agendaitem)

        agenda_item.attachment = []
        for doc in self.original_item.get('documents', []):
            attachment = MediaObject('notubiz_identifier', doc['id'])
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
