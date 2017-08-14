from ocd_backend import celery_app
# from ocd_backend import settings
from ocd_backend.mixins import OCDBackendTaskFailureMixin


class BaseExtension(OCDBackendTaskFailureMixin, celery_app.Task):
    def run(self, *args, **kwargs):
        raise NotImplementedError
