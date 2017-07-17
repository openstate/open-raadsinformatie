from PIL import Image

from ocd_backend.exceptions import UnsupportedContentType


class BaseMediaEnrichmentTask(object):
    """The base class that media enrichment tasks should inherit."""

    #: The content types that the tasks is able to process
    content_types = []

    def __init__(self, media_item, content_type, file_object, enrichment_data,
                 object_id, combined_index_doc, doc):
        if self.content_types is not '*' and content_type.lower() not\
           in self.content_types:
            raise UnsupportedContentType()

        return self.enrich_item(media_item, content_type, file_object,
                                enrichment_data, object_id, combined_index_doc,
                                doc)

    def enrich_item(self, media_item, content_type, file_object,
                    enrichment_data, object_id, combined_index_doc, doc):
        raise NotImplementedError


class MediaType(BaseMediaEnrichmentTask):
    content_types = '*'

    media_types = (
        (
            'video', (
                'video/ogg',
                'video/MP2T',
                'video/mpeg',
                'video/mp4',
                'video/webm'
            )
        ),
        (
            'image', (
                'image/jpeg',
                'image/png',
                'image/tiff'
            )
        )
    )

    def enrich_item(self, media_item, content_type, file_object,
                    enrichment_data, object_id, combined_index_doc, doc):
        item_media_type = 'unkown'

        for media_type, content_types in self.media_types:
            if content_type in content_types:
                item_media_type = media_type
                break

        enrichment_data['media_type'] = item_media_type


class ImageMetadata(BaseMediaEnrichmentTask):
    content_types = [
        'image/jpeg',
        'image/png',
        'image/tiff'
    ]

    def enrich_item(self, media_item, content_type, file_object,
                    enrichment_data, object_id, combined_index_doc, doc):
        img = Image.open(file_object)
        enrichment_data['image_format'] = img.format
        enrichment_data['image_mode'] = img.mode
        enrichment_data['resolution'] = {
            'width': img.size[0],
            'height': img.size[1],
            'total_pixels': img.size[0] * img.size[1]
        }


class ViedeoMetadata(BaseMediaEnrichmentTask):
    content_types = [
        'video/ogg',
        'video/MP2T',
        'video/mpeg',
        'video/mp4',
        'video/webm'
    ]

    def enrich_item(self, media_item, content_type, file_object,
                    enrichment_data, object_id, combined_index_doc, doc):
        pass
