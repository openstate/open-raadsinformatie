from celery import Celery
from celery import current_app
from celery.five import with_metaclass
from celery.local import Proxy
from celery.utils import gen_task_name

from ocd_backend.settings import CELERY_CONFIG

celery_app = Celery('ocd_backend', include=[
    'ocd_backend.extractors',
    'ocd_backend.extractors.ggm',
    'ocd_backend.transformers',
    'ocd_backend.transformers.ggm',
    'ocd_backend.enrichers.media_enricher',
    'ocd_backend.enrichers.media_enricher.static',
    'ocd_backend.loaders',
    'ocd_backend.loaders.file',
    'ocd_backend.tasks'
])

celery_app.conf.update(**CELERY_CONFIG)


class TaskType(type):
    """See class description of `RegisterTask`
    This code is extracted from:
    https://github.com/celery/celery/blob/v3.1.25/celery/app/task.py#L131

    Meta class for tasks.
    Automatically registers the task in the task registry (except
    if the :attr:`Task.abstract`` attribute is set).
    If no :attr:`Task.name` attribute is provided, then the name is generated
    from the module and class name.
    """
    def __new__(cls, name, bases, attrs):
        new = super(TaskType, cls).__new__
        task_module = attrs.get('__module__') or '__main__'

        # The 'app' attribute is now a property, with the real app located
        # in the '_app' attribute.  Previously this was a regular attribute,
        # so we should support classes defining it.
        app = attrs.pop('_app', None) or attrs.pop('app', None)

        # Attempt to inherit app from one the bases
        if not isinstance(app, Proxy) and app is None:
            for base in bases:
                if getattr(base, '_app', None):
                    app = base._app
                    break
            else:
                app = current_app._get_current_object()
        attrs['_app'] = app

        # - Automatically generate missing/empty name.
        task_name = attrs.get('name')
        if not task_name:
            attrs['name'] = task_name = gen_task_name(app, name, task_module)

        # - Create and register class.
        # Because of the way import happens (recursively)
        # we may or may not be the first time the task tries to register
        # with the framework.  There should only be one class for each task
        # name, so we always return the registered version.
        tasks = app._tasks
        if task_name not in tasks:
            tasks.register(new(cls, name, bases, attrs))
        instance = tasks[task_name]
        instance.bind(app)
        return instance.__class__


@with_metaclass(TaskType)
class RegisterTask(celery_app.Task):
    """Since Celery 4.0.0 Task classes are not registered automatically:
    http://docs.celeryproject.org/en/latest/whatsnew-4.0.html#the-task-base-class-no-longer-automatically-register-tasks
    In order to keep the code working this class enables Celery 3.x behaviour"""
    pass


# Monkeypatching Task in order to let it register automatically
celery_app.Task = RegisterTask
