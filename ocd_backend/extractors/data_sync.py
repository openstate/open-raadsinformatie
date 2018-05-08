from ocd_backend.extractors import BaseExtractor
from ocd_backend.utils.misc import load_object, load_sources_config
from ocd_backend.log import get_source_logger

log = get_source_logger('extractor')


class DataSyncBaseExtractor(BaseExtractor):
    """
    A data synchronizer extractor. Takes two (or more) sources, then
    reconciles data.
    """

    def __init__(self, *args, **kwargs):
        super(DataSyncBaseExtractor, self).__init__(*args, **kwargs)

        self.sources = load_sources_config(self.source_definition['sources_config'])
        self.extractors = [self._init_extractor_from_source(s) for s in self.source_definition['sources']]

    def _init_extractor_from_source(self, source_name):
        """
        Initializes an extractor from a specified source name.
        """
        try:
            source = [s for s in self.sources if s['id'] == source_name][0]
        except IndexError as e:
            source = None

        if source is None:
            return

        extractor_klass = load_object(source['extractor'])
        return extractor_klass(source)

    def match_data(self, datasets):
        """
        Match data objects from different datasets. The datasets is a list of
        generators. Expected output is a list of paired up items (a list itself)
        """
        raise NotImplementedError

    def select_data_item(self, data_items):
        """
        Selects a data item from a given set of matched data items from different
        data sets. The input is a list of tuples (each tuple is content type and object)
        while the output is a isngle of such a tuple.
        """
        raise NotImplementedError

    def run(self):
        # list comprehension to activate the generators ...
        datasets = []
        for x in self.extractors:
            try:
                data_for_dataset = [y for y in x.run()]
            except TypeError as e:
                data_for_dataset = []
            datasets.append({
                'id': x.source_definition['id'],
                'data': data_for_dataset
            })
        log.debug(datasets)

        # here we need to pair up the datasets (aka matching)
        matched_data = self.match_data(datasets)
        # log.debug(matched_data)
        num_counted = 0
        num_matched = 0
        for item_id, data_items in matched_data.iteritems():
            num_counted += 1
            if len(data_items.keys()) > 1:
                # log.debug((data_items)
                num_matched += 1
            content_type, data = self.select_data_item(data_items)
            yield content_type, data
        log.info("Matched %d out of %d items." % (num_matched, num_counted,))
