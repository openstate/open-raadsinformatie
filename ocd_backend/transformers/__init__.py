import json

from lxml import etree

from ocd_backend import celery_app
from ocd_backend.exceptions import NoDeserializerAvailable
from ocd_backend.mixins import OCDBackendTaskFailureMixin


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

    # def __init__(self, source_definition):
    #     self.source_definition = source_definition


from goapi_committee import *
from goapi_document import *
from goapi_meeting import *
