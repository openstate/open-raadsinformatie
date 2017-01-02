from hashlib import sha1
from ocd_backend.items.popolo import OrganisationItem


class CommitteeItem(OrganisationItem):

    def _get_current_permalink(self):
        return u'%s/dmus' % (self.source_definition['base_url'])

    def _get_meeting_id(self, meeting):
        hash_content = u'committee-%s' % (meeting['id'])
        return sha1(hash_content.decode('utf8')).hexdigest()

    def get_object_id(self):
        return self._get_meeting_id(self.original_item)

    def get_original_object_id(self):
        return unicode(self.original_item['id']).strip()

    def get_original_object_urls(self):
        return {"html": self._get_current_permalink()}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['id'] = unicode(self.get_object_id())

        combined_index_data['hidden'] = self.source_definition['hidden']
        combined_index_data['name'] = unicode(self.original_item['name'])
        combined_index_data['identifiers'] = [
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            },
            {
                'identifier': self.original_item['id'],
                'scheme': u'GemeenteOplossingen'
            }
        ]

        combined_index_data['classification'] = u'committee'
        combined_index_data['description'] = combined_index_data['name']

        combined_index_data['sources'] = [
            {
                'url': self._get_current_permalink,
                'note': u''
            }
        ]

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)
