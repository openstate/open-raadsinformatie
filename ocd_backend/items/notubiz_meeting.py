from ocd_backend.items import BaseItem
from ocd_backend.models import *


class NotubizMeetingItem(BaseItem):
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
        event.classification = [u'Agenda']
        event.location = self.original_item['attributes'].get('Locatie')

        # Attach the meeting to the municipality node
        event.organization = Organization(self.original_item['organisation']['id'], **source_defaults)
        event.organization.merge(collection=self.source_definition['index_name'])

        # Attach the meeting to the committee node
        event.committee = Organization(self.original_item['gremium']['id'], **source_defaults)
        # Re-attach the committee node to the municipality node
        # TODO: Why does the committee node get detached from the municipality node when meetings are attached to it?
        event.committee.parent = Organization(self.source_definition['key'], **source_defaults)
        event.committee.parent.merge(collection=self.source_definition['index_name'])

        event.agenda = []
        for item in self.original_item.get('agenda_items', []):
            if not item['order']:
                continue

            # If it's a 'label' type skip the item for now, since it only gives little information about what is to come
            if item['type'] == 'label':
                continue

            agendaitem = AgendaItem(item['id'], **source_defaults)
            agendaitem.__rel_params__ = {'rdf': '_%i' % item['order']}
            agendaitem.description = item['type_data']['attributes'][0]['value']
            agendaitem.name = self.original_item['attributes']['Titel']
            agendaitem.position = self.original_item['order']
            agendaitem.parent = event
            agendaitem.start_date = event.start_date

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
            attachment.identifier_url = doc['self']  # Trick to use the self url for enrichment
            attachment.original_url = doc['url']
            attachment.name = doc['title']
            attachment.date_modified = doc['last_modified']
            event.attachment.append(attachment)

        return event
