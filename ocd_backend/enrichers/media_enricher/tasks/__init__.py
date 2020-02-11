class BaseEnrichmentTask:
    """The singleton base class that enrichment tasks should inherit."""
    def __new__(cls, source_definition):
        if not hasattr(cls, 'instance'):
            cls.instance = super(BaseEnrichmentTask, cls).__new__(cls)
        return cls.instance

    def __init__(self, source_definition):
        self.source_definition = source_definition

    def enrich_item(self, item, file_object):
        raise NotImplementedError
