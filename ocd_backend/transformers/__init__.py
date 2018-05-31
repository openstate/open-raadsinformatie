import json

from lxml import etree

from ocd_backend import celery_app
from ocd_backend.exceptions import NoDeserializerAvailable
from ocd_backend.mixins import OCDBackendTaskFailureMixin
from ocd_backend.utils.misc import load_object


class BaseTransformer(OCDBackendTaskFailureMixin, celery_app.Task):
    def run(self, *args, **kwargs):
        """Start transformation of a single item.

        This method is called by the extractor and expects args to
        contain the content-type and the original item (as a string).
        Kwargs should contain the ``source_definition`` dict.

        :returns: the output of :py:meth:`~BaseTransformer.transform_item`
        """
        self.source_definition = kwargs['source_definition']
        self.item_class = load_object(kwargs['source_definition']['item'])
        self.run_node = kwargs.get('run_node')

        item = self.deserialize_item(*args)  # pylint: disable=no-value-for-parameter
        return self.transform_item(*args, item=item)  # pylint: disable=no-value-for-parameter

    @staticmethod
    def deserialize_item(raw_item_content_type, raw_item):
        if raw_item_content_type == 'application/json':
            return json.loads(raw_item)
        elif raw_item_content_type == 'application/xml':
            return etree.XML(raw_item)
        elif raw_item_content_type == 'application/html':
            return etree.HTML(raw_item)
        else:
            raise NoDeserializerAvailable('Item with content_type %s'
                                          % raw_item_content_type)

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
                               raw_item, item, self.run_node)

        return item.object_data
