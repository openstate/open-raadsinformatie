import os
from PIL import Image

from ocd_backend.exceptions import UnsupportedContentType
from ocd_backend.models import *
from ocd_backend.utils.file_parsing import FileToTextMixin


class BaseMediaEnrichmentTask(object):
    """The base class that media enrichment tasks should inherit."""

    #: The content types that the tasks is able to process
    content_types = []

    def __init__(self, media_item, content_type, file_object):
        if self.content_types is not '*' and content_type.lower() not \
                in self.content_types:
            raise UnsupportedContentType()

        self.enrich_item(media_item, content_type, file_object)

    def enrich_item(self, media_item, content_type, file_object):
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

    def enrich_item(self, media_item, content_type, file_object):
        item_media_type = 'unkown'

        for media_type, content_types in self.media_types:
            if content_type in content_types:
                item_media_type = media_type
                break

        media_item.content_type = item_media_type


class ImageMetadata(BaseMediaEnrichmentTask):
    content_types = [
        'image/jpeg',
        'image/png',
        'image/tiff'
    ]

    def enrich_item(self, media_item, content_type, file_object):
        img = Image.open(file_object)
        media_item.encoding_format = img.format
        media_item.width, media_item.height = img.size

        # exif = PropertyValue(None)
        # exif.name = 'Color Type'
        # exif.value = img.mode
        # media_item.exif_data = exif


class ViedeoMetadata(BaseMediaEnrichmentTask):
    content_types = [
        'video/ogg',
        'video/MP2T',
        'video/mpeg',
        'video/mp4',
        'video/webm'
    ]

    def enrich_item(self, media_item, content_type, file_object):
        pass


class FileToText(BaseMediaEnrichmentTask, FileToTextMixin):
    content_types = '*'

    def enrich_item(self, media_item, content_type, file_object):
        path = os.path.realpath(file_object.name)
        media_item.text = self.file_to_text(path)

        if media_item.text:
            self.process_text(media_item.text, media_item)
        else:
            # meta = Metadata()
            # meta.status = u'Unable to download or parse this file'
            # media_item.meta = meta
            pass

    def process_text(self, text, media_item):
        pass
