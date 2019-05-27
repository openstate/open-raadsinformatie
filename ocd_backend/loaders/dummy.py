from ocd_backend.log import get_source_logger
from ocd_backend.models.serializers import JsonSerializer
from ocd_backend.loaders import BaseLoader

log = get_source_logger('dummy_loader')


class DummyLoader(BaseLoader):
    """
    Prints the item to the console, for debugging purposes.
    """

    def load_item(self, doc):
        log.debug('=' * 50)
        log.debug('%s %s %s' % ('=' * 4, doc.get_ori_identifier(), '=' * 4))
        log.debug('%s %s %s' % ('-' * 20, 'doc', '-' * 25))
        log.debug(JsonSerializer().serialize(doc))
        log.debug('=' * 50)

    @staticmethod
    def run_finished(run_identifier):
        log.debug('*' * 50)
        log.debug('Finished run {}'.format(run_identifier))
        log.debug('*' * 50)
