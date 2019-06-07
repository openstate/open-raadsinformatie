import json
from datetime import datetime

from ocd_backend.exceptions import FieldNotAvailable
from ocd_backend.models import Metadata
from ocd_backend.models.misc import Uri
from ocd_backend.models.definitions import Mapping


class BaseItem(object):
    """Represents a single extracted and transformed item.

    :param source_definition: The configuration of a single source in
        the form of a dictionary (as defined in the settings).
    :type source_definition: dict
    :param data_content_type: The content-type of the data retrieved
        from the source (e.g. ``application/json``).
    :type data_content_type: str
    :param data: The data in it's original format, as retrieved
        from the source.
    :type data: unicode
    :param item: the deserialized item retrieved from the source.
    :param processing_started: The datetime we started processing this
        item. If ``None``, the current datetime is used.
    :type processing_started: datetime or None
    """

    def __init__(self, source_definition, data_content_type, data, item, run_node, processing_started=None,
                 final_try=False):
        self.source_definition = source_definition
        self.data_content_type = data_content_type
        self.data = data
        self.original_item = item
        self.run_node = run_node
        self.final_try = final_try

        # On init, all data should be available to construct self.meta
        # and self.combined_item
        self._construct_object_meta(processing_started)
        self._store_object_data()

    def _construct_object_meta(self, processing_started=None):
        source_defaults = {
            'source': 'ori/meta',
            'source_id_key': 'identifier',
            'organization': 'ori',
        }

        # meta = Metadata(1)
        #
        # if not processing_started:
        #     meta.processing_started = datetime.now()
        #
        # meta.source_id = unicode(self.source_definition['id'])
        # meta.collection = self.source_definition['key']
        # meta.rights = self.get_rights()
        #
        # self.meta = meta

    def _store_object_data(self):
        object_data = self.get_object_model()
        # object_data.meta = self.meta

        object_data.save()

        self.object_data = object_data

    def get_object_model(self):
        """Construct the document that should be inserted into the index
        belonging to the item's source.
        """
        raise NotImplementedError

    def get_rights(self):
        """Retrieves the rights of the item as defined by the source.
        With 'rights' we mean information about copyright, licenses,
        instructions for reuse, etcetera. "Creative Commons Zero" is an
        example of a possible value of rights.

        This method should be implemented by the class that inherits from
        :class:`.BaseItem`.

        :rtype: unicode.
        """
        raise NotImplementedError


# todo needs revision v1
# class LocalDumpItem(BaseItem):
#     """
#     Represents an Item extracted from a local dump
#     """
#
#     def get_collection(self):
#         collection = self.original_item['_source'].get('meta', {}) \
#             .get('collection')
#         if not collection:
#             raise FieldNotAvailable('collection')
#         return collection
#
#     def get_rights(self):
#         rights = self.original_item['_source'].get('meta', {}).get('rights')
#         if not rights:
#             raise FieldNotAvailable('rights')
#         return rights
#
#     def get_object_model(self):
#         combined_index_data = self.original_item['_source'] \
#             .get('combined_index_data')
#         if not combined_index_data:
#             raise FieldNotAvailable('combined_index_data')
#
#         data = json.loads(combined_index_data)
#         data.pop('meta')
#         # Cast datetimes
#         for key, value in data.iteritems():
#             if self.combined_index_fields.get(key) == datetime:
#                 data[key] = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
#
#         return data
#
#     def get_all_text(self):
#         """
#         Returns the content that is stored in the combined_index_data.all_text
#         field, and raise a `FieldNotAvailable` exception when it is not
#         available.
#
#         :rtype: unicode
#         """
#         combined_index_data = json.loads(self.original_item['_source']
#                                          .get('combined_index_data', {}))
#         all_text = combined_index_data.get('all_text')
#         if not all_text:
#             raise FieldNotAvailable('combined_index_data.all_text')
#         return all_text
#
#     def get_index_data(self):
#         """Restore all fields that are originally indexed.
#
#         :rtype: dict
#         """
#         return self.original_item.get('_source', {})
