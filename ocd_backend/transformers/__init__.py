import json
from hashlib import sha1

from lxml import etree

from ocd_backend import celery_app
from ocd_backend import settings
from ocd_backend.exceptions import NoDeserializerAvailable
from ocd_backend.mixins import OCDBackendTaskFailureMixin
from ocd_backend.utils.misc import load_object


class BaseTransformer(OCDBackendTaskFailureMixin, celery_app.Task):

    def run(self, *args, **kwargs):
        """Start transformation of a single item.

        This method is called by the extractor and expects args to
        contain the content-type and the original item (as a string).
        Kwargs should contain the ``source_definition`` dict.

        :type raw_item_content_type: string
        :param raw_item_content_type: the content-type of the data
            retrieved from the source (e.g. ``application/json``)
        :type raw_item: string
        :param raw_item: the data in it's original format, as retrieved
            from the source (as a string)
        :param source_definition: The configuration of a single source in
            the form of a dictionary (as defined in the settings).
        :type source_definition: dict.
        :returns: the output of :py:meth:`~BaseTransformer.transform_item`
        """
        self.source_definition = kwargs['source_definition']
        self.item_class = load_object(kwargs['source_definition']['item'])

        item = self.deserialize_item(*args)
        return self.transform_item(*args, item=item)

    def deserialize_item(self, raw_item_content_type, raw_item):
        if raw_item_content_type == 'application/json':
            return json.loads(raw_item)
        elif raw_item_content_type == 'application/xml':
            return etree.XML(raw_item)
        else:
            raise NoDeserializerAvailable('Item with content_type %s'
                                          % raw_item_content_type)

    def add_resolveable_media_urls(self, item):
        """For each item in ``media_urls``, add a ``url`` variant that
        can be resolved by the OCD REST API."""
        if 'media_urls' in item.combined_index_data:
            for media_url in item.combined_index_data['media_urls']:
                hashed_url = sha1(media_url['original_url']).hexdigest()
                media_url['url'] = '%s/%s' % (settings.RESOLVER_BASE_URL, hashed_url)

    def transform_item(self, raw_item_content_type, raw_item, item):
        """Transforms a single item.

        The output of this method serves as input of a loader.

        :type raw_item_content_type: string
        :param raw_item_content_type: the content-type of the data
            retrieved from the source (e.g. ``application/json``)
        :type raw_item: string
        :param raw_item: the data in it's original format, as retrieved
            from the source (as a string)
        :type item: dict
        :param item: the deserialized item
        :returns: a tuple containing the new object id, the item structured
            for the combined index (as a dict) and the item item structured
            for the source specific index.
        """
        item = self.item_class(self.source_definition, raw_item_content_type,
                               raw_item, item)

        self.add_resolveable_media_urls(item)

        return (
            item.get_combined_object_id(),
            item.get_object_id(),
            item.get_combined_index_doc(),
            item.get_index_doc()
        )
