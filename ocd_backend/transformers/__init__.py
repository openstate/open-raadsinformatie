import json

from lxml import etree

from ocd_backend import celery_app
from ocd_backend.exceptions import NoDeserializerAvailable
from ocd_backend.mixins import OCDBackendTaskFailureMixin
from ocd_backend.utils.misc import load_object


class BaseTransformer(OCDBackendTaskFailureMixin, celery_app.Task):

    @staticmethod
    def deserialize_item(content_type, raw_item):
        if content_type == 'application/json':
            return json.loads(raw_item)
        elif content_type == 'application/xml':
            return etree.XML(raw_item)
        elif content_type == 'application/html':
            return etree.HTML(raw_item)
        else:
            raise NoDeserializerAvailable('Item with content_type %s' % content_type)

    def start(self, content_type, raw_item, entity, source_item, **kwargs):
        """Start transformation of a single item."""

        self.source_definition = kwargs['source_definition']
        item_class = load_object(self.source_definition['item'])

        deserialized_item = self.deserialize_item(content_type=content_type, raw_item=raw_item)

        transformed_item = item_class(deserialized_item=deserialized_item,
                                      entity=entity,
                                      source_definition=self.source_definition).transform()

        transformed_item.save()

        return transformed_item


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=(Exception,), retry_backoff=True)
def transformer(self, *args, **kwargs):
    return self.start(*args, **kwargs)
