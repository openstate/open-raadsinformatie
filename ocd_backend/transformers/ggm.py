from ocd_backend.transformers import BaseTransformer
from ocd_backend.utils.misc import load_object, strip_namespaces


class GegevensmagazijnBaseTransformer(BaseTransformer):

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

        item

        :param source_definition: The configuration of a single source in
            the form of a dictionary (as defined in the settings).
        :type source_definition: dict.
        :returns: the output of :py:meth:`~BaseTransformer.transform_item`
        """

        # Vaag gebeuren met dubbele nesting waardoor *args niet meer werkt
        args = args[0]

        self.source_definition = kwargs['source_definition']

        if 'item' in kwargs:
            item = kwargs['item']
        else:
            item = self.deserialize_item(*args)

        return self.transform_item(*args, item=strip_namespaces(item))

    def transform_item(self, raw_item_content_type, raw_item, item):
        root_name = item.xpath("local-name()")

        if root_name in self.source_definition['mapping']:
            item_source = self.source_definition['mapping'][root_name]
            item_class = item_source['item_class']
        else:
            #raise Exception("item_class was not found for %s in the source_definition mapping!" % root_name)
            print "%s not in mapping" % root_name
            return [] # <-- kan dit voor problemen zorgen?

        items = []
        if 'sub_items' in item_source:
            for path in item_source['sub_items']:
                for subitem in item.xpath(path):
                    items += self.transform_item(raw_item_content_type, raw_item, subitem)

        item = load_object(item_class)(self.source_definition, raw_item_content_type,
                               raw_item, item)

        self.add_resolveable_media_urls(item)

        doc_type = item_source['doc_type']

        return [(
            item.get_combined_object_id(),
            item.get_object_id(),
            item.get_combined_index_doc(),
            item.get_index_doc(),
            doc_type
        )] + items
