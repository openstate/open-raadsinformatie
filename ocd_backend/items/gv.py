from datetime import datetime
from hashlib import sha1
# import iso8601

from ocd_backend.items import BaseItem
from ocd_backend.models import *


class GreenValleyItem(BaseItem):
    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def _get_documents_as_media_urls(self):
        media_urls = {}
        if u'attachmentlist' in self.original_item:
            for att_key, att in self.original_item.get(u'attachmentlist', {}).iteritems():
                if att[u'objecttype'] == 'AGENDAPAGE':
                    continue

                url = "https://staten.zuid-holland.nl/dsresource?objectid=%s" % (
                    att[u'objectid'].encode('utf8'),)

                doc_hash = unicode(
                    sha1(url + ':' + att[u'objectname'].encode('utf8')).hexdigest())
                media_urls[doc_hash] = {
                    "note": att[u'objectname'],
                    "original_url": url
                }
        else:
            default = self.original_item['default']
            if default[u'objecttype'] != 'AGENDAPAGE':
                url = "https://staten.zuid-holland.nl/dsresource?objectid=%s" % (
                    default[u'objectid'].encode('utf8'),)

                doc_hash = unicode(
                    sha1(url + ':' + default[u'objectname'].encode('utf8')).hexdigest()
                )
                media_urls[doc_hash] = {
                    "note": default[u'objectname'],
                    "original_url": url
                }

        if media_urls:
            return media_urls.values()
        else:
            return None

    def get_object_model(self):
        source_defaults = {
            'source': 'greenvalley',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        meeting = self.original_item[u'default']

        event = Meeting(meeting[u'objectid'], **source_defaults)

        if meeting.get(u'bis_vergaderdatum', u'').strip() != u'':
            event.start_date = datetime.fromtimestamp(
                float(meeting[u'bis_vergaderdatum']) +
                (float(meeting.get(u'bis_starttijduren', '0') or '0') * 3600) +
                (float(meeting.get(u'bis_starttijdminuten', '0') or '0') * 60))
            event.end_date = datetime.fromtimestamp(
                float(meeting[u'bis_vergaderdatum']) +
                (float(meeting.get(u'bis_eindtijduren', '0') or '0') * 3600) +
                (float(meeting.get(u'bis_eindtijdminuten', '0') or '0') * 60))
        elif u'publishdate' in meeting:
            event.start_date = datetime.fromtimestamp(
                float(meeting[u'publishdate']))
            event.end_date = datetime.fromtimestamp(
                float(meeting[u'publishdate']))

        event.name = meeting[u'objectname']

        objecttype2classification = {
            'agenda': 'Agenda',
            'agendapage': 'Agendapunt',
            'bestuurlijkstuk': 'Bestuurlijk stuk',
            'notule': 'Verslag',
            'ingekomenstuk': 'Ingekomen stuk',
            'antwoordstuk': 'Antwoord'  # ?
        }
        event.classification = [u'Agenda']
        try:
            event.classification = [unicode(
                objecttype2classification[meeting[u'objecttype'].lower()])]
        except LookupError:
            event.classification = [unicode(
                meeting[u'objecttype'].capitalize())]
        event.description = meeting[u'objectname']

        try:
            event.location = meeting[u'bis_locatie'].strip()
        except (AttributeError, KeyError):
            pass

        try:
            event.organization = Organization(
                meeting[u'bis_orgaan'], **source_defaults)
            event.committee = Organization(
                meeting[u'bis_orgaan'], **source_defaults)
        except LookupError as e:
            pass

        # object_model['last_modified'] = iso8601.parse_date(
        #    self.original_item['last_modified'])

        # if self.original_item['canceled']:
        #     event.status = EventCancelled()
        # elif self.original_item['inactive']:
        #     event.status = EventUnconfirmed()
        # else:
        #     event.status = EventConfirmed()
        event.status = EventConfirmed()

        event.attachment = []
        for doc in self._get_documents_as_media_urls():
            attachment = MediaObject(doc['original_url'], **source_defaults)
            attachment.identifier_url = doc['original_url']  # Trick to use the self url for enrichment
            attachment.original_url = doc['original_url']
            attachment.name = doc['note']
            event.attachment.append(attachment)

        return event


class GreenValleyMeeting(GreenValleyItem):
    def get_object_model(self):
        event = super(GreenValleyMeeting, self).get_object_model()

        source_defaults = {
            'source': 'greenvalley',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        event.agenda = []

        children = []
        for a, v in self.original_item.get(u'SETS', {}).iteritems():
            if v[u'objecttype'].lower() == u'agendapage':
                result = {u'default': v}
                children.append(result)

        for item in children:
            meeting = item[u'default']
            agendaitem = AgendaItem(meeting['objectid'], **source_defaults)
            agendaitem.__rel_params__ = {
                'rdf': '_%i' % int(meeting['agendapagenumber'])}
            agendaitem.description = meeting[u'objectname']
            agendaitem.name = meeting[u'objectname']
            agendaitem.position = int(meeting['agendapagenumber'])

            event.agenda.append(agendaitem)

        return event
