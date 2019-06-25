from ocd_backend.items import BaseItem
from ocd_backend.models import *
from ocd_backend.log import get_source_logger

log = get_source_logger('notubiz_meeting')


class NotubizMeetingItem(BaseItem):
    def get_object_model(self):
        source_defaults = {
            'source': 'notubiz',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        event = Meeting(self.original_item['id'], **source_defaults)
        event.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)

        event.start_date = self.original_item['plannings'][0]['start_date']
        event.end_date = self.original_item['plannings'][0]['end_date']
        event.name = self.original_item['attributes'].get('Titel', 'Vergadering %s' % event.start_date)
        event.classification = [u'Agenda']
        event.location = self.original_item['attributes'].get('Locatie')

        # Attach the meeting to the municipality node
        event.organization = TopLevelOrganization(self.source_definition['key'], **source_defaults)

        # Attach the meeting to the committee node
        event.committee = Organization(self.original_item['gremium']['id'], **source_defaults)
        event.committee.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)

        # Re-attach the committee node to the municipality node
        event.committee.subOrganizationOf = TopLevelOrganization(self.source_definition['key'], **source_defaults)

        event.agenda = []
        for item in self.original_item.get('agenda_items', []):
            if not item['order']:
                continue

            # If it's a 'label' type skip the item for now, since it only gives little information about what is to come
            if item['type'] == 'label':
                continue

            agendaitem = AgendaItem(item['id'], **source_defaults)
            agendaitem.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)

            agendaitem.__rel_params__ = {'rdf': '_%i' % item['order']}
            agendaitem.description = item['type_data']['attributes'][0]['value']
            agendaitem.name = self.original_item['attributes']['Titel']
            agendaitem.position = self.original_item['order']
            agendaitem.parent = event
            agendaitem.start_date = event.start_date

            agendaitem.attachment = []
            for doc in item.get('documents', []):
                attachment = MediaObject(doc['id'], **source_defaults)
                attachment.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)

                attachment.identifier_url = doc['self']  # Trick to use the self url for enrichment
                attachment.original_url = doc['url']
                attachment.name = doc['title']
                attachment.date_modified = doc['last_modified']
                attachment.isReferencedBy = agendaitem
                agendaitem.attachment.append(attachment)

            event.agenda.append(agendaitem)

        # object_model['last_modified'] = iso8601.parse_date(
        #    self.original_item['last_modified'])

        if 'canceled' in self.original_item and self.original_item['canceled']:
            log.info('Found a Notubiz event with status EventCancelled: %s' % str(event.values))
            event.status = EventCancelled()
        elif 'inactive' in self.original_item and self.original_item['inactive']:
            log.info('Found a Notubiz event with status EventUncomfirmed: %s' % str(event.values))
            event.status = EventUnconfirmed()
        else:
            event.status = EventConfirmed()

        event.attachment = []
        for doc in self.original_item.get('documents', []):
            attachment = MediaObject(doc['id'], **source_defaults)
            attachment.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)

            attachment.identifier_url = doc['self']  # Trick to use the self url for enrichment
            attachment.original_url = doc['url']
            attachment.name = doc['title']
            attachment.date_modified = doc['last_modified']
            attachment.isReferencedBy = event
            event.attachment.append(attachment)

        return event
