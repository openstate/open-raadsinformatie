import logging
import logging.config

from ocd_backend.settings import LOGGING, RELEASE_STAGE, BUGSNAG_APIKEY

if BUGSNAG_APIKEY:
    import bugsnag
    from bugsnag.handlers import BugsnagHandler
    from .utils.bugsnag_celery import connect_failure_handler

    bugsnag.configure(
        api_key=BUGSNAG_APIKEY,
        project_root="/opt/ori",
        release_stage=RELEASE_STAGE,
    )

    connect_failure_handler()

    logger = logging.getLogger("bugsnag")
    handler = BugsnagHandler()
    # send only WARN-level logs and above
    handler.setLevel(logging.WARN)
    logger.addHandler(handler)


logging.config.dictConfig(LOGGING)


def get_source_logger(name=None):
    return logging.getLogger('ocd_backend')
