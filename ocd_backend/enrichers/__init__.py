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

        results = list()
        for item in args:
            combined_object_id, object_id, combined_index_doc, doc, doc_type = item
            try:
                self.enrich_item(
                    doc['enrichments'],
                    object_id,
                    combined_index_doc,
                    doc,
                    doc_type
                )

                results.append((combined_object_id, object_id,
                                combined_index_doc, doc, doc_type))
            except SkipEnrichment as e:
                log.info('Skipping %s for %s, reason: %s'
                         % (self.__class__.__name__, object_id, e.message))
                results.append(
                    (combined_object_id, object_id, combined_index_doc, doc,
                     doc_type))
            except:
                log.exception('Unexpected error, skipping %s for %s'
                              % (self.__class__.__name__, object_id))
                results.append(
                    (combined_object_id, object_id, combined_index_doc, doc,
                     doc_type))

        return results

    def enrich_item(self, enrichments, object_id, combined_index_doc, doc,
                    doc_type):
        """Enriches a single item.

        This method should be implemented by the class that inherits
        from :class:`.BaseEnricher`. The method should modify and return
        the passed ``enrichments`` dictionary. The contents of the
        ``combined_index_doc`` and ``doc`` can be used to generate the
        enrichments.

        :param enrichments: the dict that should be modified by the
            enrichment task. It is possible that this dictionary already
            contains enrichments from previous tasks.
        :type enrichments: dict
        :param object_id: the identifier of the item that is being enriched.
        :type object_id: str
        :param combined_index_doc: the 'combined index' representation
            of the item.
        :type combined_index_doc: dict
        :param doc: the collection specific index representation of the
            item.
        :type doc: dict
        :returns: a modified enrichments dictionary.
        """
        raise NotImplemented
