from datetime import datetime

from ocd_backend.items.popolo import PersonItem, OrganisationItem


class PopitBaseItem(object):
    """
    Base class for importing things from a Popit instance.
    """

    ignored_list_fields = {
        'memberships': [
            # FIXME: start and end dates for memberships borked due to ES configuration (?)
            'start_date', 'end_date',
            'url', 'html_url', 'contact_details', 'images', 'links'
        ],
        # FIXME: start and end dates for memberships borked due to ES configuration (?)
        # 'start_date', 'end_date'
    }

    def get_object_id(self):
        return unicode(self.original_item['id'])

    def get_original_object_id(self):
        return self.get_object_id()

    def get_original_object_urls(self):
        try:
            return self.original_item['meta']['original_object_urls']
        except KeyError as e:
            return {'html': self.original_item['html_url']}

    def get_rights(self):
        try:
            return self.original_item['meta']['rights']
        except KeyError as e:
            return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

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
