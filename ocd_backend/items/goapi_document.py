import iso8601
import pytz

from ocd_backend.items import BaseItem
from ocd_backend.models import *
from ocd_backend.log import get_source_logger

log = get_source_logger('goapi_meeting')


class GemeenteOplossingenDocumentItem(BaseItem):
    def _get_current_permalink(self):
        api_version = self.source_definition.get('api_version', 'v1')
        base_url = '%s/%s' % (
            self.source_definition['base_url'], api_version,)

        return u'%s/documents/%i' % (base_url, self.original_item[u'id'],)

    def _get_documents_as_media_urls(self, documents):
        current_permalink = self._get_current_permalink()

        output = []
        for document in documents:
            # sleep(1)
            url = current_permalink
            output.append({
                'url': url,
                'note': document[u'filename']})
        return output

    def transform(self):
        source_defaults = {
            'source': 'gemeenteoplossingen',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        event = Meeting(self.original_item[u'id'], **source_defaults)
        event.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)

        event.organization = TopLevelOrganization(self.source_definition['key'], **source_defaults)

        try:
            date_tz = pytz.timezone(
                self.original_item['publicationDate']['timezone'])
        except Exception:
            date_tz = None
        start_date = iso8601.parse_date(
            self.original_item['publicationDate']['date'].replace(' ', 'T'))
        if date_tz is not None:
            try:
                start_date = start_date.astimezone(date_tz)
            except Exception:
                pass

        event.start_date = start_date
        event.end_date = event.start_date  # ?
        event.name = self.original_item[u'description']
        event.classification = [self.original_item['documentTypeLabel']]
        event.description = self.original_item[u'description']

        event.attachment = []
        for doc in self._get_documents_as_media_urls(
            self.original_item.get('documents', [])
        ):
            attachment = MediaObject(doc['url'], **source_defaults)
            attachment.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)

            attachment.identifier_url = doc['url']  # Trick to use the self url for enrichment
            attachment.original_url = doc['url']
            attachment.name = doc['note']
            attachment.isReferencedBy = event
            event.attachment.append(attachment)

        return event
