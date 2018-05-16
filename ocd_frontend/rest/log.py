import logging


def get_source_logger(name=None):
    logger = logging.getLogger('ocd_frontend')

    if name:
        logger = logging.LoggerAdapter(logger, {'source': name})

    return logger
