import urllib
from datetime import datetime

from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.mixins import OCDBackendTaskSuccessMixin, OCDBackendTaskFailureMixin
from ocd_backend.models.misc import Url
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
        self.start_time = kwargs.get('start_time')

        for _, item in iterate(args):
            self.load_item(item)

    def load_item(self, doc):
        raise NotImplementedError

    def add_metadata(self, model, is_original):
        from ocd_backend.models import Activity
        meta = Activity()

        try:
            meta.had_primary_source = Url(model.canonical_iri)
        except AttributeError:
            pass

        try:
            if is_original:
                meta.original_identifier = str(model.canonical_id)
            else:
                meta.reference_identifier = str(model.canonical_id)
        except AttributeError:
            pass

        meta.ori_identifier = Url(model.get_ori_identifier() + '#meta')
        if model.cached_path:
            meta.used = Url('{}/{}'.format(settings.RESOLVER_BASE_URL, urllib.parse.quote(model.cached_path)))
        meta.generated = model.get_ori_identifier()
        meta.same_as = Url(model.source_iri)
        meta.started_at_time = self.start_time
        meta.ended_at_time = datetime.now()
        meta.app_semver = settings.APP_VERSION

        model.was_generated_by = meta
