from celery.utils.time import get_exponential_backoff_interval
from functools import wraps

from ocd_backend.log import get_source_logger
from ocd_backend.settings import AUTORETRY_EXCEPTIONS, AUTORETRY_RETRY_BACKOFF, AUTORETRY_RETRY_BACKOFF_MAX, RETRY_MAX_RETRIES

log = get_source_logger('retry_task')

def retry_task(fun):
    """
    A decorator to use with celery tasks to retry tasks after an exception occurred.
    When `autoretry_for` is used, all exceptions are reported to Sentry, also when they
    are going to be retried. This is not desired - only when retrying the task a number of
    times fails it should be reported.
    The tasks that appeared in Sentry most often have been replaced by this decorator.
    If there are more tasks that pollute Sentry, use this decorator and remove `autoretry_for`,
    `retry_backoff` and `retry_backoff_max` from the @celery_app.task decorator.
    With a AUTORETRY_RETRY_BACKOFF=30 and number of retries = 9:
        1: 60
        2: 120
        3: 240
        4: 480
        5: 960
        6: 1920
        7: 3840
        8: 7680
        9: 15360
        Total: 30660 seconds
    """
    @wraps(fun)
    def handle_retry(self, *args, **kwargs):
        try:
            return fun(self, *args, **kwargs)
        except tuple(AUTORETRY_EXCEPTIONS) as e:
            if is_retryable_error(e):
                try:
                    log.info(f'Retry attempt n = {self.request.retries} for error ({e.__class__.__name__}):\n{str(e)}')
                    countdown = get_exponential_backoff_interval(
                        factor=AUTORETRY_RETRY_BACKOFF,
                        retries=self.request.retries,
                        maximum=AUTORETRY_RETRY_BACKOFF_MAX)
                    raise self.retry(countdown=countdown)
                except self.MaxRetriesExceededError:
                    log.error(f'Maximum number of retries reached for error ({e.__class__.__name__}):\n{str(e)}')
                    raise

    return handle_retry

def is_retryable_error(error, url = None, retries_sofar = None):
    error_string = str(error)
    retryable = True

    if 'too many 500 error responses' in error_string:
        retryable = False
    if 'NameResolutionError' in error_string:
        retryable = False
    if ('itinnovationday.nl' in error_string or 'azavista.com' in error_string or 'www.bestuur.centrum.amsterdam.nl' in error_string) and \
        ('ConnectTimeoutError' in error_string or 'Connection refused' in error_string):
        retryable = False
    if 'www.mantelzorgpleinalmere.nl' in error_string and 'SSLV3_ALERT_HANDSHAKE_FAILURE' in error_string:
        retryable = False
    if 'Read timed out' in error_string and url is not None and 'api.notubiz.nl/document/7357190/2' in url:
        retryable = False
    if 'Read timed out' in error_string and '.raadsinformatie.nl' in error_string and 'module_filter' in error_string:
        retryable = False
    if 'Read timed out' in error_string and '.notubiz.nl' in error_string and 'module_filter' in error_string:
        retryable = False
    if 'Read timed out' in error_string and 'www.gelderland.nl' in error_string:
        retryable = False
    if 'Connection to loket.breda.nl timed out' in error_string and 'fGegevensFormulierCombi' in error_string:
        retryable = False
    if 'EOF occurred in violation of protocol' in error_string and 'bestuursakkoord.s-hertogenbosch.nl' in error_string:
        retryable = False
    if 'Connection to www.deventerondernemersevent.nl timed out' in error_string:
        retryable = False
    if 'Connection to www.ggdhartvoorbrabantjaarverslag.nl timed out' in error_string:
        retryable = False
    if 'ConnectTimeoutError' in error_string and ('217.149.64.42' in error_string or 'financien.purmerend.nl' in error_string):
        retryable = False
    if 'www.ouderenombudsman.nl' in error_string or 'www.nctb.nl' in error_string or 'www.vng.abfsoftware.nl' in error_string or \
        'festival.bestuurskunde.nl' in error_string:
        retryable = False
    if 'veenendaalsekrant.nl' in error_string or '.mijnstem.nl' in error_string:
        retryable = False

    # If maximum number of retries has been reached see if we should stop retrying
    if retryable and retries_sofar == RETRY_MAX_RETRIES:
        if stop_retrying(error):
            retryable = False

    if not retryable:
        log.info(f'Non-retryable error caught ({error.__class__.__name__}):\n{error_string}')
    
    return retryable

# Frequently urls are returned that are not pointing to active sites anymore. Some of those urls were added
# to `is_retryable_error` above. This method is a more general approach:
#   - if the error implies a connection error
#   - and if it is not a call to one of the suppliers
#   - -> then stop retrying, otherwise keep on retrying
def stop_retrying(error):
    error_string = str(error)

    connection_error = \
        'ConnectTimeoutError' in error_string or \
        'Connection refused' in error_string or \
        'NameResolutionError' in error_string or \
        'Network unreachable' in error_string

    is_a_supplier_call = \
        '.ibabs.eu' in error_string or \
        '.notubiz.nl' in error_string or \
        '.parlaeus.nl' in error_string or \
        '.qualigraf.nl' in error_string or \
        'raad.' in error_string or \
        'raadsinformatie.' in error_string or \
        '/api/' in error_string

    if connection_error and not is_a_supplier_call:
        return True

    return
