from pprint import pprint

from ocd_backend.extractors import BaseExtractor
from ocd_backend.utils.misc import load_object, load_sources_config


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


    def pair_data(self, datasets):
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
        datasets = [y for x in self.extractors for y in x.run()]
        pprint(datasets)

        # here we need to pair up the datasets (aka matching)
        paired_data = self.pair_data(datasets)

        for data_items in paired_data:
            content_type, data = self.select_data_item(data_items)
            yield content_type, data
