from PIL import Image

from ocd_backend.enrichers.media_enricher.tasks import BaseEnrichmentTask


class ImageMetadata(BaseEnrichmentTask):
    def enrich_item(self, item, file_object):
        img = Image.open(file_object)
        item.encoding_format = img.format
        item.width, item.height = img.size
