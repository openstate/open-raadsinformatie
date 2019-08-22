import bugsnag

from ocd_backend import celery_app
from ocd_backend.exceptions import SkipEnrichment
from ocd_backend.log import get_source_logger
from ocd_backend.utils.misc import iterate
from ocd_backend.models.enricher_log import EnricherLog

log = get_source_logger('enricher')


class BaseEnricher(celery_app.Task):
    """The base class that enrichers should inherit."""

    def start(self, *args, **kwargs):
        """Start enrichment of a single item.

        This method is called by the transformer or by another enricher
        and expects args to contain a transformed (and possibly enriched)
        item. Kwargs should contain the ``source_definition`` dict.

        :returns: the output of :py:meth:`~BaseEnricher.enrich_item`
        """

        self.source_definition = kwargs['source_definition']
        self.enricher_settings = kwargs['enricher_settings']
        self.enricher_log = EnricherLog()

        for _, doc in iterate(args):
            for model in doc.traverse():
                try:
                    if not hasattr(model, 'enricher_task'):
                        continue
                except AttributeError:
                    continue

                try:
                    resource_id = int(model.ori_identifier.rsplit('/')[3])
                    enricher_class = self.__name__
                    task = model.enricher_task
                    if not self.enricher_log.check(resource_id, enricher_class, task):
                        self.enrich_item(model)
                        self.enricher_log.insert(resource_id, enricher_class, task)
                    else:
                        log.info('Skipping "%s.%s" for resource id %s - '
                                 'task already executed.' % (enricher_class, task, resource_id))
                        continue
                except SkipEnrichment as e:
                    bugsnag.notify(e, severity="info")
                    log.info('Skipping %s, reason: %s'
                             % (self.__class__.__name__, e.message))
                except IOError as e:
                    # In the case of an IOError, disk space or some other
                    # serious problem might occur.
                    bugsnag.notify(e, severity="error")
                    log.critical(e)
                    raise
                except Exception as e:
                    bugsnag.notify(e, severity="warning")
                    log.warning('Unexpected error: %s, reason: %s' % (self.__class__.__name__, e))
                    raise

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
