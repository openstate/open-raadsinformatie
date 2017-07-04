import os
from PIL import Image

from ocd_backend.exceptions import UnsupportedContentType
from ocd_backend.utils.file_parsing import FileToTextMixin


class BaseMediaEnrichmentTask(object):
    """The base class that media enrichment tasks should inherit."""

    #: The content types that the tasks is able to process
    content_types = []

    def __init__(self, media_item, content_type, file_object, enrichment_data,
                 object_id, combined_index_doc, doc, doc_type):
        if self.content_types is not '*' and content_type.lower() not\
           in self.content_types:
            raise UnsupportedContentType()

        self.enrich_item(media_item, content_type, file_object,
                         enrichment_data, object_id, combined_index_doc, doc,
                         doc_type)

    def enrich_item(self, media_item, content_type, file_object,
                    enrichment_data, object_id, combined_index_doc, doc,
                    doc_type):
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
                    enrichment_data, object_id, combined_index_doc, doc,
                    doc_type):
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
                    enrichment_data, object_id, combined_index_doc, doc,
                    doc_type):
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
                    enrichment_data, object_id, combined_index_doc, doc,
                    doc_type):
        pass


class FileToText(BaseMediaEnrichmentTask, FileToTextMixin):
    content_types = '*'

    def enrich_item(self, media_item, content_type, file_object,
                    enrichment_data, object_id, combined_index_doc, doc,
                    doc_type):

        path = os.path.realpath(file_object.name)
        self.text = self.file_to_text(path)
        self.format_text()

        if self.text:
            source = {
                'url': media_item['original_url'],
                'note': media_item.get('note', u''),
                'description': self.text
            }
        else:
            source = {
                'url': media_item['original_url'],
                'note': u'Unable to download or parse this file'
            }

        if 'sources' not in combined_index_doc:
            combined_index_doc['sources'] = []
        combined_index_doc['sources'].append(source)

        if 'sources' not in doc:
            doc['sources'] = []
        doc['sources'].append(source)

    def format_text(self):
        pass
