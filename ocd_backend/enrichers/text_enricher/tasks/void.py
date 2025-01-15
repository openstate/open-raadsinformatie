from ocd_backend.enrichers.text_enricher.tasks import BaseEnrichmentTask

class VoidEnrichtmentTask(BaseEnrichmentTask):
    def enrich_item(self, item, metadata):
        pass
