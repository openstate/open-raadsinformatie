from __future__ import division, print_function, absolute_import

import bugsnag
from celery.signals import task_failure


def failure_handler(sender, task_id, exception, args, kwargs, traceback, einfo,
                    **kw):
    """
    Overriding configuration in bugsnag.celery in order to set the severity
    to warning instead of error.
    """
    task = {
        "task_id": task_id,
        "args": args,
        "kwargs": kwargs
    }

    bugsnag.auto_notify(exception, traceback=traceback,
                        context=sender.name,
                        extra_data=task,
                        severity='warning',  # adding this to original code
                        severity_reason={
                            'type': 'unhandledExceptionMiddleware',
                            'attributes': {
                                'framework': 'Celery'
                            }
                        })


def connect_failure_handler():
    """
    Connect the bugsnag failure_handler to the Celery
    task_failure signal
    """
    task_failure.connect(failure_handler, weak=False)
