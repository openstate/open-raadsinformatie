from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.items import BaseItem
from ocd_backend.models import *
from ocd_backend.utils.api import FrontendAPIMixin
from ocd_backend.utils.file_parsing import FileToTextMixin


class Meeting(BaseItem, HttpRequestMixin, FrontendAPIMixin, FileToTextMixin):
    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        event = Event('notubiz_identifier', self.original_item['id'])
        event.start_date = self.original_item['plannings'][0]['start_date']
        event.end_date = self.original_item['plannings'][0]['end_date']
        event.name = 'Vergadering %s %s' % (self.original_item['attributes'].get('Titel'), event.start_date)
        # event.description =
        event.classification = [u'Agenda']
        event.location = self.original_item['attributes'].get('Locatie')

        event.organization = Organization.get_or_create(name=self.source_definition['municipality'])
        event.organization.notubiz_identifier = self.original_item['organisation']['id']

        event.committee = Organization.get_or_create(notubiz_identifier=self.original_item['gremium']['id'])

        event.agenda = []
        for item in self.original_item.get('agenda_items', []):
            if not item['order']:
                continue

            agendaitem = AgendaItem.get_or_create(notubiz_identifier=item['id'])
            agendaitem.__rel_params__ = {'rdf': '_%i' % item['order']}
            event.agenda.append(agendaitem)

        # object_model['last_modified'] = iso8601.parse_date(
        #    self.original_item['last_modified'])

        if self.original_item['canceled']:
            event.status = EventCancelled
        elif self.original_item['inactive']:
            event.status = EventInactive
        else:
            event.status = EventConfirmed

        event.attachment = []
        for doc in self.original_item.get('documents', []):
            attachment = Attachment('notubiz_identifier', doc['id'])
            attachment.original_url = doc['url']
            attachment.name = doc['title']
            event.attachment.append(attachment)

        return event
