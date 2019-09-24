from datetime import datetime

from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.mixins import OCDBackendTaskSuccessMixin, OCDBackendTaskFailureMixin
from ocd_backend.utils.misc import iterate

log = get_source_logger('loader')


class BaseLoader(OCDBackendTaskSuccessMixin, OCDBackendTaskFailureMixin,
                 celery_app.Task):
    """The base class that other loaders should inherit."""

    def start(self, *args, **kwargs):
        """Start loading of a single item.

        This method is called by the transformer and expects args to
        contain the output of the transformer as a tuple.
        Kwargs should contain the ``source_definition`` dict.

        :returns: the output of :py:meth:`~BaseTransformer.transform_item`
        """
        self.source_definition = kwargs['source_definition']

        for _, item in iterate(args):
            self.post_processing(item)
            self.load_item(item)

    def load_item(self, doc):
        raise NotImplementedError

    @staticmethod
    def post_processing(doc):
        # Add the 'processing.finished' datetime to the documents
        finished = datetime.now()
        # doc.Meta.processing_finished = finished
