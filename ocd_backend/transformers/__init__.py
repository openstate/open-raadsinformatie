import json

from lxml import etree
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ocd_backend import celery_app
from ocd_backend.exceptions import NoDeserializerAvailable
from ocd_backend.mixins import OCDBackendTaskFailureMixin
from ocd_backend.utils.misc import load_object
from ocd_backend.models.postgres_models import Source
from ocd_backend import settings


class BaseTransformer(OCDBackendTaskFailureMixin, celery_app.Task):

    @staticmethod
    def deserialize_item(raw_item_content_type, raw_item):
        if raw_item_content_type == 'application/json':
            return json.loads(raw_item)
        elif raw_item_content_type == 'application/xml':
            return etree.XML(raw_item)
        elif raw_item_content_type == 'application/html':
            return etree.HTML(raw_item)
        else:
            raise NoDeserializerAvailable('Item with content_type %s' % raw_item_content_type)

    def start(self, raw_item_content_type, raw_item, source_item, **kwargs):
        """Start transformation of a single item."""

        self.source_definition = kwargs['source_definition']
        item_class = load_object(self.source_definition['item'])

        original_item = self.deserialize_item(raw_item_content_type=raw_item_content_type,
                                              raw_item=raw_item)

        transformed_item = item_class(original_item=original_item,
                                      source_definition=self.source_definition).transform()

        transformed_item.save()

        self.update_source(ori_id=transformed_item.get_short_identifier(),
                           entity=original_item['entity'],
                           source_item=source_item)

        return transformed_item

    def update_source(self, ori_id, entity, source_item):
        connection_string = 'postgresql://%s:%s@%s/%s' % (
                            settings.POSTGRES_USERNAME,
                            settings.POSTGRES_PASSWORD,
                            settings.POSTGRES_HOST,
                            settings.POSTGRES_DATABASE)
        engine = create_engine(connection_string)
        Session = sessionmaker(bind=engine)

        session = Session()
        source = session.query(Source).filter(Source.resource_ori_id == ori_id).one()
        source.type = self.source_definition['source_type']
        source.entity = entity
        session.commit()
        session.close()


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=(Exception,), retry_backoff=True)
def transformer(self, *args, **kwargs):
    return self.start(*args, **kwargs)
