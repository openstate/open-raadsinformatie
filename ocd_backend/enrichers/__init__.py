import bugsnag

from ocd_backend import celery_app
from ocd_backend.exceptions import SkipEnrichment
from ocd_backend.log import get_source_logger
from ocd_backend.utils.misc import iterate

log = get_source_logger('enricher')


class BaseEnricher(celery_app.Task):
    """The base class that enrichers should inherit."""

    def run(self, *args, **kwargs):
        """Start enrichment of a single item.

        This method is called by the transformer or by another enricher
        and expects args to contain a transformed (and possibly enriched)
        item. Kwargs should contain the ``source_definition`` dict.

        :returns: the output of :py:meth:`~BaseEnricher.enrich_item`
        """

        self.source_definition = kwargs['source_definition']
        self.enricher_settings = kwargs['enricher_settings']

        for _, doc in iterate(args):
            for model in doc.traverse():
                try:
                    if not hasattr(model, 'enricher_task'):
                        continue
                except AttributeError:
                    continue

                try:
                    self.enrich_item(model)
                except SkipEnrichment as e:
                    bugsnag.notify(e, severity="info")
                    log.info('Skipping %s, reason: %s'
                             % (self.__class__.__name__, e.message))
                except IOError as e:
                    # In the case of an IOError, disk space or some other
                    # serious problem might occur.
                    bugsnag.notify(e, severity="error")
                    log.critical(e)
                except Exception as e:
                    bugsnag.notify(e, severity="warning")
                    log.warning('Unexpected error: %s, reason: %s' % (self.__class__.__name__, e))

        return args

    def enrich_item(self, item):
        """Enriches a single item.

        This method should be implemented by the class that inherits
        from :class:`.BaseEnricher`. The method should modify or add
        attributes of the supplied item.

        :param item: the collection specific index representation of the
            item.
        :type item: object
        """
        raise NotImplementedError
