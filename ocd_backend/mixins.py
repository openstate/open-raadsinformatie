from ocd_backend.utils.misc import load_object


class OCDBackendTaskMixin:
    """
    This Mixin provides a cleanup method that is called from the classes that
    inherit from it: this way, we can provide cleanup behaviour that is either
    executed when a task fails (for instance, when it is somewhere in the middle
    of a chain), or when a task is successfully executed (for instance, when a
    loader successfully inserted its data into the storage system.

    It loads a `Task` that is defined by a dotted path in `sources.json`.
    """

    def cleanup(self, **kwargs):
        cleanup_task = load_object(self.source_definition.get('cleanup'))
        cleanup_task.delay(**kwargs)


class OCDBackendTaskFailureMixin(OCDBackendTaskMixin):
    """Add this mixin to a task that should execute `self.cleanup` when the
    Task fails."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self.cleanup(**kwargs)


class OCDBackendTaskSuccessMixin(OCDBackendTaskMixin):
    """Add this mixin to a task that should execute `self.cleanup` when the
    Task succeeds."""

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        self.cleanup(**kwargs)
