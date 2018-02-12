from hashlib import sha1

from ocd_backend.items.popolo import EventItem
from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.utils.api import FrontendAPIMixin
from ocd_backend.utils.file_parsing import FileToTextMixin
from ocd_backend.models import *


def get_meeting_id(item_id):
    hash_content = u'meeting-%s' % item_id
    return unicode(sha1(hash_content.decode('utf8')).hexdigest())


class Meeting(EventItem, HttpRequestMixin, FrontendAPIMixin, FileToTextMixin):

    @staticmethod
    def _get_meetingitem_id(item_id):
        from ocd_backend.items.notubiz_meetingitem import get_meetingitem_id
        return get_meetingitem_id(item_id)

    def _get_documents_as_media_urls(self):
        media_urls = {}
        for doc in self.original_item.get('documents', []):
            doc_hash = unicode(sha1(
                (doc.get('url', u'') + u':' + doc.get('title', u'')).decode(
                    'utf8')).hexdigest())
            media_urls[doc_hash] = {
                "url": "/v0/resolve/",
                "note": doc['title'],
                "original_url": doc['url']
            }
        if media_urls:
            return media_urls.values()
        else:
            return None

    def _get_current_permalink(self):
        return u'%s/events/meetings/%i' % (
            self.source_definition['base_url'], self.original_item['id'])

    def get_object_id(self):
        return get_meeting_id(self.original_item['id'])

    def get_original_object_id(self):
        return unicode(self.original_item['id']).strip()

    def get_original_object_urls(self):
        return {"html": self._get_current_permalink()}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        event = Event('notubiz_identifier', self.original_item['id'])
        event.startDate = self.original_item['plannings'][0]['start_date']
        event.endDate = self.original_item['plannings'][0]['end_date']
        event.name = 'Vergadering %s %s' % (self.original_item['attributes'].get('Titel'), event.startDate)
        # event.description =
        event.classification = u'Agenda'
        event.location = self.original_item['attributes'].get('Locatie')
        event.organization = Organization(
            'notubiz_identifier',
            self.original_item['organisation']['id'],
            temporary=True,
        )

        event.agenda = []
        for item in self.original_item.get('agenda_items', []):
            agendaitem = AgendaItem(
                'notubiz_identifier',
                item['id'],
                rel_params={'rdf': '_%i' % item['order']},
                temporary=True,
            )
            agendaitem.description = self.original_item['attributes'].get('Omschrijving') or \
                                     self.original_item['attributes'].get('Tekst')

            event.agenda.append(agendaitem)


        # object_model['last_modified'] = iso8601.parse_date(
        #    self.original_item['last_modified'])

        if self.original_item['canceled']:
            event.status = EventStatusType.EventCancelled
        elif self.original_item['inactive']:
            event.status = EventStatusType.EventInactive
        else:
            event.status = EventStatusType.EventConfirmed

        event.attachment = []
        for doc in self.original_item.get('documents', []):
            attachment = Attachment('notubiz_identifier', doc['id'])
            attachment.original_url = doc['url']
            attachment.name = doc['title']
            event.attachment.append(attachment)

        return event

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
