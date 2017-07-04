from lxml import etree

from ocd_backend.log import get_source_logger
from ocd_backend.transformers import BaseTransformer
from ocd_backend.utils.misc import load_object, strip_namespaces

log = get_source_logger('transformer')


class GegevensmagazijnTransformer(BaseTransformer):

    def run(self, *args, **kwargs):
        args = args[0]

        self.source_definition = kwargs['source_definition']
        item = self.deserialize_item(*args)

        return self.transform_item(*args, item=strip_namespaces(item))

    def transform_item(self, raw_item_content_type, raw_item, item,
                       class_name=False):

        if not class_name:
            class_name = item.xpath("local-name()")

        if class_name in self.source_definition['mapping']:
            item_source = self.source_definition['mapping'][class_name]
            item_class = item_source['item']
        else:
            log.info('Skipping %s, does not exist in mapping' % class_name)
            return []

        items = list()
        if 'sub_items' in item_source:
            for key, path in item_source['sub_items'].items():
                for sub_item in item.xpath(path):
                    items += self.transform_item(raw_item_content_type,
                                                 etree.tostring(sub_item),
                                                 sub_item, class_name=key)

        item_class = load_object(item_class)
        item = item_class(self.source_definition, raw_item_content_type,
                          raw_item, item, unicode(item_source['doc_type']))

        self.add_resolveable_media_urls(item)

        return [(
            item.get_combined_object_id(),
            item.get_object_id(),
            item.get_combined_index_doc(),
            item.get_index_doc(),
            item.doc_type
        )] + items
