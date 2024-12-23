from celery.utils.time import get_exponential_backoff_interval
from functools import wraps

from ocd_backend.log import get_source_logger
from ocd_backend.settings import AUTORETRY_EXCEPTIONS, AUTORETRY_RETRY_BACKOFF, AUTORETRY_RETRY_BACKOFF_MAX

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
    """
    @wraps(fun)
    def handle_retry(self, *args, **kwargs):
        try:
            return fun(self, *args, **kwargs)
        except tuple(AUTORETRY_EXCEPTIONS) as e:
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
