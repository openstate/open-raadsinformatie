import logging
import logging.config

from ocd_backend.settings import LOGGING

logging.config.dictConfig(LOGGING)


def get_source_logger(name=None):
    return logging.getLogger('ocd_backend')
