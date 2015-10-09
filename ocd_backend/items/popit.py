from datetime import datetime

from ocd_backend.items.popolo import PersonItem, OrganisationItem


class PopitBaseItem(object):
    """
    Base class for importing things from a Popit instance.
    """

    ignored_list_fields = {
        'memberships': [
            'url', 'html_url', 'contact_details', 'images', 'links'
        ]
    }

    def get_object_id(self):
        return unicode(self.original_item['id'])

    def get_original_object_id(self):
        return self.get_object_id()

    def get_original_object_urls(self):
        return self.original_item['meta']['original_object_urls']

    def get_rights(self):
        return self.original_item['meta']['rights']

    def get_collection(self):
        return self.original_item['meta']['collection']

    def get_combined_index_data(self):
        combined_index_data = {
            'hidden': self.source_definition['hidden']
        }

        for field in self.combined_index_fields:
            if field not in self.original_item:
                continue

            if self.combined_index_fields[field] == unicode:
                combined_index_data[field] = unicode(
                    self.original_item[field])
            elif self.combined_index_fields[field] == datetime:
                combined_index_data[field] = iso8601.parse_date(
                    self.original_item[field])
            elif self.combined_index_fields[field] == list:
                if field in self.ignored_list_fields:
                    combined_index_data[field] = [
                        {k: v for k, v in l.iteritems() if k not in self.ignored_list_fields[field]} for l in self.original_item[field]]
                else:
                    combined_index_data[field] = self.original_item[field]
            else:
                combined_index_data[field] = self.original_item[field]

        return combined_index_data

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []

        return u' '.join(text_items)


class PopitPersonItem(PopitBaseItem, PersonItem):
    """
    Imports persons from a popit instance.
    """
    pass


class PopitOrganisationItem(PopitBaseItem, OrganisationItem):
    """
    Imports organizations from a popit instance.
    """
    pass
