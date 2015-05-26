from datetime import datetime
import locale
import re

from ocd_backend.items import BaseItem

class PRIDItem(BaseItem):
    # Override the default generating of a hash object ID based on the
    # original object id and object urls, and simply use the PRID
    def get_object_id(self):
        return self.original_item['prid']

    # Override the default combined object ID, which is the same as the
    # hash object ID. Instead use the object ID based on the PRID and
    # prepend it with the index name.
    def get_combined_object_id(self):
        return '%s_%s' % (
            self.source_definition['index_name'],
            self.get_object_id()
        )

    def get_original_object_id(self):
        return self.original_item['prid']

    def get_original_object_urls(self):
        locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')
        broadcast_date = datetime.strptime(
            self.original_item['broadcast_date'],
            '%a %d %b %Y %H:%M'
        )
        locale.resetlocale(locale.LC_TIME)

        return {"html": "http://npo.nl/%s/%s/%s" % (
            self.original_item['program_slug'],
            broadcast_date.strftime('%d-%m-%Y'),
            self.original_item['prid']
        )}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return u'PRID'

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['hidden'] = self.source_definition['hidden']

        if self.original_item['prid']:
            combined_index_data['prid'] = self.original_item['prid']

        if self.original_item['program_name']:
            combined_index_data['title'] = self.original_item['program_name']

        if ('broadcast_date' in self.original_item
                and self.original_item['broadcast_date']):
            locale.setlocale(locale.LC_TIME, 'nl_NL.UTF-8')
            broadcast_date = datetime.strptime(
                self.original_item['broadcast_date'],
                '%a %d %b %Y %H:%M'
            )
            locale.resetlocale(locale.LC_TIME)
            combined_index_data['date'] = broadcast_date

            combined_index_data['date_granularity'] = 12

        if 'broadcasters' in self.original_item:
            combined_index_data['authors'] = self.original_item['broadcasters']

        if 'image' in self.original_item:
            media_urls = []
            for image in self.original_item['image']:
                # Extract the width and height from the URL
                match = re.match(
                    '.*/c(\d+)x(\d+)/.*\.png', image
                )
                if match:
                    media_urls.append(
                        {
                            'original_url': image,
                            'content_type': 'image/png',
                            'width': match.group(1),
                            'height': match.group(2)
                        }
                    )
                else:
                    media_urls.append(
                        {
                            'original_url': image,
                            'content_type': 'image/png'
                        }
                    )

            combined_index_data['media_urls'] = media_urls

        return combined_index_data

    def get_index_data(self):
        return self.original_item

    def get_all_text(self):
        text_items = []

        if self.original_item['program_name']:
            text_items.append(self.original_item['program_name'])

        if self.original_item['program_slug']:
            text_items.append(self.original_item['program_slug'])

        if self.original_item['prid']:
            text_items.append(self.original_item['prid'])

        if 'broadcasters' in self.original_item:
            for broadcaster in self.original_item['broadcasters']:
                text_items.append(broadcaster)

        return u' '.join(text_items)
