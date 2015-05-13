from datetime import datetime

from ocd_backend.items import BaseItem

class NPOJournalistiekItem(BaseItem):
    def get_original_object_id(self):
        return self.original_item['Id']

    def get_original_object_urls(self):
        return {}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return u'NPO Journalistiek'

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['hidden'] = self.source_definition['hidden']

        if self.original_item['Title']:
            combined_index_data['title'] = self.original_item['Title']

        if 'Body' in self.original_item and self.original_item['Body']:
            combined_index_data['description'] = self.original_item['Body']

        if 'Date' in self.original_item and self.original_item['Date']:
            strptime_string = '%Y-%m-%dT%H:%M:%S'
            if len(self.original_item['Date']) > 19:
                strptime_string = '%Y-%m-%dT%H:%M:%S.%f'
            combined_index_data['date'] = datetime.strptime(
                self.original_item['Date'],
                strptime_string
            )
            combined_index_data['date_granularity'] = 14

        if self.original_item['Broadcasters']:
            authors = []
            for broadcaster in self.original_item['Broadcasters']:
                if broadcaster['Name'] and broadcaster['Name'] not in authors:
                    authors.append(broadcaster['Name'])

            if authors:
                combined_index_data['authors'] = authors

        if self.original_item['Image']:
            combined_index_data['media_urls'] = [
                {
                    'original_url': 'http://statischecontent.nl/img/16x9/1000x/%s.jpg' % (self.original_item['Image']['Key']),
                    'content_type': 'image/jpeg',
                    'width': 1000,
                    'height': 563
                },
                {
                    'original_url': 'http://statischecontent.nl/img/1x1/880x/%s.jpg' % (self.original_item['Image']['Key']),
                    'content_type': 'image/jpeg',
                    'width': 880,
                    'height': 880
                },
                {
                    'original_url': 'http://statischecontent.nl/img/4x3/880x/%s.jpg' % (self.original_item['Image']['Key']),
                    'content_type': 'image/jpeg',
                    'width': 880,
                    'height': 660
                },
                {
                    'original_url': 'http://statischecontent.nl/img/3x4/x1600/%s.jpg' % (self.original_item['Image']['Key']),
                    'content_type': 'image/jpeg',
                    'width': 1200,
                    'height': 1600
                }
            ]

        return combined_index_data

    def get_index_data(self):
        return self.original_item

    def get_all_text(self):
        text_items = []

        if self.original_item['Title']:
            text_items.append(self.original_item['Title'])

        if self.original_item['ListTitle']:
            text_items.append(self.original_item['ListTitle'])

        if self.original_item['Body']:
            text_items.append(self.original_item['Body'])

        if self.original_item['Summary']:
            text_items.append(self.original_item['Summary'])

        if self.original_item['Mid']:
            text_items.append(self.original_item['Mid'])

        if self.original_item['ProgramTitle']:
            text_items.append(self.original_item['ProgramTitle'])

        if self.original_item['Summary']:
            text_items.append(self.original_item['Summary'])

        if self.original_item['Locations']:
            for location in self.original_item['Locations']:
                if location['Country']:
                    text_items.append(location['Country'])

                if location['Name']:
                    text_items.append(location['Name'])

        if self.original_item['Broadcasters']:
            for broadcaster in self.original_item['Broadcasters']:
                if broadcaster['Name']:
                    text_items.append(broadcaster['Name'])

        if self.original_item['Categories']:
            for category in self.original_item['Categories']:
                if category['Name']:
                    text_items.append(category['Name'])

        if self.original_item['Dossiers']:
            for dossier in self.original_item['Dossiers']:
                if dossier['Name']:
                    text_items.append(dossier['Name'])

        return u' '.join(text_items)
