import iso8601

from ocd_backend.items import BaseItem
from ocd_backend.models import *
from ocd_backend.log import get_source_logger

log = get_source_logger('goapi_meeting')


class GemeenteOplossingenMeetingItem(BaseItem):
    def _get_current_permalink(self):
        api_version = self.source_definition.get('api_version', 'v1')
        base_url = '%s/%s' % (
            self.source_definition['base_url'], api_version,)

        return u'%s/meetings/%i' % (base_url, self.original_item[u'id'],)

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def _get_documents_as_media_urls(self, documents):
        current_permalink = self._get_current_permalink()

        output = []
        for document in documents:
            # sleep(1)
            url = u"%s/documents/%s" % (current_permalink, document['id'])
            output.append({
                'url': url,
                'note': document[u'filename']})
        return output

    def get_object_model(self):
        source_defaults = {
            'source': 'gemeenteoplossingen',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        event = Meeting(self.original_item[u'id'], **source_defaults)

        # dates in v1 have a time in them and in v2 they don't
        if ':' in self.original_item['date']:
            start_date = self.original_item['date']
        else:
            start_date = "%sT%s:00" % (
                self.original_item['date'],
                self.original_item.get('startTime', '00:00',))

        event.start_date = iso8601.parse_date(start_date)
        event.end_date = event.start_date  # ?

        # Some meetings are missing a name because some municipalities do not always fill the description field.
        # In this case we create the name from the name of the commission and the start date of the meeting.
        # See issue #124.
        if self.original_item['description'] == '':
            event.name = 'Vergadering - %s - %s' % (self.original_item[u'dmu'][u'name'], event.start_date)
        else:
            event.name = self.original_item[u'description']

        event.classification = [u'Agenda']
        event.description = self.original_item[u'description']

        try:
            event.location = self.original_item[u'location'].strip()
        except (AttributeError, KeyError):
            pass

        # Attach the meeting to the municipality node
        event.organization = Organization(self.source_definition['key'], **source_defaults)
        event.organization.merge(collection=self.source_definition['key'])

        # Attach the meeting to the committee node. GO always lists either the name of the committee or 'Raad'
        # if it is a non-committee meeting so we can attach it to a committee node without any extra checks
        # as opposed to iBabs
        event.committee = Organization(self.original_item[u'dmu'][u'id'], **source_defaults)
        # Re-attach the committee node to the municipality node
        # TODO: Why does the committee node get detached from the municipality node when meetings are attached to it?
        event.committee.subOrganizationOf = Organization(self.source_definition['key'], **source_defaults)
        event.committee.subOrganizationOf.merge(collection=self.source_definition['key'])

        # object_model['last_modified'] = iso8601.parse_date(
        #    self.original_item['last_modified'])

        # TODO: This is untested so we log any cases that are not the default
        if 'canceled' in self.original_item and self.original_item['canceled']:
            log.info('Found a GOAPI event with status EventCancelled: %s' % str(event.values))
            event.status = EventCancelled()
        elif 'inactive' in self.original_item and self.original_item['inactive']:
            log.info('Found a GOAPI event with status EventUnconmfirmed: %s' % str(event.values))
            event.status = EventUnconfirmed()
        else:
            event.status = EventConfirmed()

        event.agenda = []
        for item in self.original_item.get('items', []):
            if not item['sortorder']:
                continue

            agendaitem = AgendaItem(item['id'], **source_defaults)
            agendaitem.__rel_params__ = {'rdf': '_%i' % item['sortorder']}
            agendaitem.description = item['description']
            agendaitem.name = '%s: %s' % (item['number'], item['title'],)
            agendaitem.position = item['sortorder']
            agendaitem.parent = event
            agendaitem.start_date = event.start_date
            agendaitem.attachment = []

            for doc in self._get_documents_as_media_urls(
                item.get('documents', [])
            ):
                attachment = MediaObject(doc['url'], **source_defaults)
                attachment.identifier_url = doc['url']  # Trick to use the self url for enrichment
                attachment.original_url = doc['url']
                attachment.name = doc['note']
                attachment.isReferencedBy = agendaitem
                agendaitem.attachment.append(attachment)

            event.agenda.append(agendaitem)

        event.attachment = []
        for doc in self._get_documents_as_media_urls(
            self.original_item.get('documents', [])
        ):
            attachment = MediaObject(doc['url'], **source_defaults)
            attachment.identifier_url = doc['url']  # Trick to use the self url for enrichment
            attachment.original_url = doc['url']
            attachment.name = doc['note']
            attachment.isReferencedBy = event
            event.attachment.append(attachment)

        return event
