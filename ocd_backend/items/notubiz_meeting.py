from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.items import BaseItem
from ocd_backend.models import *
from ocd_backend.utils.api import FrontendAPIMixin
from ocd_backend.utils.file_parsing import FileToTextMixin
from ocd_backend.models.misc import Uri
from ocd_backend.models.definitions import Mapping


class NotubizMeeting(BaseItem):
    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        source_defaults = {
            'source': 'notubiz',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        event = Meeting(self.original_item['id'], **source_defaults)
        event.start_date = self.original_item['plannings'][0]['start_date']
        event.end_date = self.original_item['plannings'][0]['end_date']
        event.name = self.original_item['attributes'].get('Titel', 'Vergadering %s' % event.start_date)
        # event.description =
        event.classification = [u'Agenda']
        event.location = self.original_item['attributes'].get('Locatie')

        event.organization = Organization(self.original_item['organisation']['id'], **source_defaults)
        event.organization.connect(name=self.source_definition['sitename'])
        event.committee = Organization(self.original_item['gremium']['id'], **source_defaults)

        event.agenda = []
        for item in self.original_item.get('agenda_items', []):
            if not item['order']:
                continue

            agendaitem = AgendaItem(item['id'], **source_defaults)
            agendaitem.__rel_params__ = {'rdf': '_%i' % item['order']}
            agendaitem.description = item['type_data']['attributes'][0]['value']
            event.agenda.append(agendaitem)

        # object_model['last_modified'] = iso8601.parse_date(
        #    self.original_item['last_modified'])

        if self.original_item['canceled']:
            event.status = EventCancelled()
        elif self.original_item['inactive']:
            event.status = EventUnconfirmed()
        else:
            event.status = EventConfirmed()

        event.attachment = []
        for doc in self.original_item.get('documents', []):
            attachment = MediaObject(doc['id'], **source_defaults)
            attachment.original_url = doc['url']
            attachment.name = doc['title']
            event.attachment.append(attachment)

        return event
