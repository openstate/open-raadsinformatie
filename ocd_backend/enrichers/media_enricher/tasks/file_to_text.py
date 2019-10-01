import cStringIO
import os
from tempfile import NamedTemporaryFile

import simplejson as json

from ocd_backend.utils.file_parsing import file_parser
from ocd_backend.utils.http import GCSCachingMixin
from . import BaseEnrichmentTask


class FileToText(BaseEnrichmentTask, GCSCachingMixin):
    bucket_name = 'ori-enriched'
    default_content_type = 'application/json'

    def enrich_item(self, item, file_object):
        if self.exists(item.identifier_url):
            _, _, cached_file = self.download_cache(item.identifier_url)
            try:
                item.text = json.load(cached_file)['data']
                return
            except (ValueError, KeyError):
                # No json could be decoded or data not found, pass and parse again
                pass
            finally:
                cached_file.close()

        # Make sure file_object is actually on the disk for pdf parsing
        temporary_file = None
        if isinstance(file_object, cStringIO.OutputType):
            temporary_file = NamedTemporaryFile(delete=True)
            temporary_file.write(file_object.read())
            temporary_file.seek(0, 0)
            file_object = temporary_file

        if os.path.exists(file_object.name):
            path = os.path.realpath(file_object.name)
            item.text = file_parser(path, max_pages=100)

        if hasattr(item, 'text') and item.text:
            self.process_text(item.text, item)

            # Save the enriched version to the ori-enriched bucket
            data = json.dumps({
                'data': item.text,
                'pages': len(item.text),
            })
            self.save(item.identifier_url, data)
        else:
            pass

        if temporary_file:
            temporary_file.close()

    def process_text(self, text, item):
        pass
