from requests import exceptions

from ocd_backend.app import celery_app
from ocd_backend.exceptions import SkipEnrichment
from ocd_backend.log import get_source_logger
from ocd_backend.utils.misc import iterate

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

        for _, doc in iterate(args):
            for model in doc.traverse():
                try:
                    if not model.enricher_task:
                        continue
                except AttributeError:
                    continue

                try:
                    metadata = {
                        'key': self.source_definition["key"],
                        'key_type': self.source_definition["source_type"],
                        'key_name': self.source_definition["source_name"],
                        'supplier': self.source_definition["supplier"]
                    }
                    self.enrich_item(model, metadata)
                except SkipEnrichment as e:
                    log.info(f'[{self.source_definition["key"]}] Skipping enrichment, {self.__class__.__name__}, reason: {e}')
                except exceptions.ConnectionError as e:
                    log.warning(f'[{self.source_definition["key"]}] ConnectionError occurred for enrich_item, reason: {e}')
                    raise
                except IOError as e:
                    # In the case of an IOError, disk space or some other
                    # serious problem might occur.
                    log.critical(f'[{self.source_definition["key"]}] IOError occurred, {self.__class__.__name__}, reason: {e}')
                    raise
                except Exception as e:
                    log.warning(f'[{self.source_definition["key"]}] Unexpected error, {self.__class__.__name__}, reason: {e}')
                    raise

        return args

    def enrich_item(self, item, metadata):
        """Enriches a single item.

        This method should be implemented by the class that inherits
        from :class:`.BaseEnricher`. The method should modify or add
        attributes of the supplied item.

        :param item: the collection specific index representation of the
            item.
        :type item: object
        """
        raise NotImplementedError
