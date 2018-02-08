from ocd_backend import celery_app
from ocd_backend.exceptions import SkipEnrichment
from ocd_backend.log import get_source_logger

log = get_source_logger('enricher')


class BaseEnricher(celery_app.Task):
    """The base class that enrichers should inherit."""

    def run(self, *args, **kwargs):
        """Start enrichment of a single item.

        This method is called by the transformer or by another enricher
        and expects args to contain a transformed (and possibly enriched)
        item. Kwargs should contain the ``source_definition`` dict.

        :param item: The item tuple as returned by a transformer or by
            a previously runned enricher.
        :param source_definition: The configuration of a single source in
            the form of a dictionary (as defined in the settings).
        :type source_definition: dict.
        :param enricher_settings: The settings for the requested enricher,
            as provided in the source definition.
        :type enricher_settings: dict.
        :returns: the output of :py:meth:`~BaseEnricher.enrich_item`
        """

        args = args[0]
        self.source_definition = kwargs['source_definition']
        self.enricher_settings = kwargs['enricher_settings']

        # Make a single list if items is a single item
        if type(args) == tuple:
            args = [args]

        for doc in args:
            try:
                for prop, value in doc.properties(props=True, rels=True):
                    try:
                        if not value.Meta.enricher_task:
                            continue
                    except AttributeError:
                        continue

                    self.enrich_item(value)

            except SkipEnrichment as e:
                log.info('Skipping %s for %s, reason: %s'
                         % (self.__class__.__name__, doc.get_ori_id(), e.message))
            except Exception, e:
                print e
                log.exception('Unexpected error, skipping %s for %s'
                              % (self.__class__.__name__, doc.get_ori_id()))

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
        raise NotImplemented
