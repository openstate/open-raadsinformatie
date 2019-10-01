class BaseEnrichmentTask(object):
    """The singleton base class that enrichment tasks should inherit."""
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(BaseEnrichmentTask, cls).__new__(cls)
        return cls.instance

    def enrich_item(self, item, file_object):
        raise NotImplementedError
