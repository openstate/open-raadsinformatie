import cStringIO
import simplejson as json
import os
from tempfile import NamedTemporaryFile

from PIL import Image

from ocd_backend.exceptions import UnsupportedContentType
from ocd_backend.settings import TEMP_DIR_PATH
from ocd_backend.utils.file_parsing import file_parser
from ocd_backend.utils.http import GCSCachingMixin


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


class FileToText(BaseMediaEnrichmentTask, GCSCachingMixin):
    content_types = '*'

    bucket_name = 'ori-enriched'
    default_content_type = 'application/json'

    def enrich_item(self, media_item, content_type, file_object):
        if self.exists(media_item.identifier_url):
            _, _, cached_file = self.download_cache(media_item.identifier_url)
            try:
                media_item.text = json.load(cached_file)['data']
                return
            except (ValueError, KeyError):
                # No json could be decoded or data not found, pass and parse again
                pass
            finally:
                cached_file.close()

        # Make sure file_object is actually on the disk for pdf parsing
        temporary_file = None
        if isinstance(file_object, cStringIO.OutputType):
            temporary_file = NamedTemporaryFile(dir=TEMP_DIR_PATH)
            temporary_file.write(file_object.read())
            temporary_file.seek(0, 0)
            file_object = temporary_file

        if os.path.exists(file_object.name):
            path = os.path.realpath(file_object.name)
            media_item.text = file_parser(path, max_pages=20)

        if media_item.text:
            self.process_text(media_item.text, media_item)

            # Save the enriched version to the ori-enriched bucket
            data = json.dumps({
                'data': media_item.text,
                'pages': len(media_item.text),
            })
            self.save(media_item.identifier_url, data)
        else:
            pass

        if temporary_file:
            temporary_file.close()

    def process_text(self, text, media_item):
        pass
