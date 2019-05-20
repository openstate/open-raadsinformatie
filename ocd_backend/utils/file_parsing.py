import tempfile
from urllib2 import HTTPError

import magic
import pdfparser.poppler as pdf
import tika.parser as parser

from ocd_backend.log import get_source_logger

log = get_source_logger('file_parser')


def file_parser(fname, pages=None):
    if magic.from_file(fname, mime=True) == 'application/pdf':
        try:
            result_pages = []
            i = 0
            d = pdf.Document(fname, quiet=True)
            for i, p in enumerate(d, start=1):
                text_array = []
                for f in p:
                    for b in f:
                        for l in b:
                            text_array.append(unicode(l.text))
                result_pages.append('\n'.join(text_array))

                if i >= pages:  # break after x pages
                    break

            log.debug("Processed %i pages (%i max)", i, pages)
            return result_pages
        except:
            # reraise everything
            raise
    else:
        try:
            content = parser.from_file(fname)['content']
            return (content or '').encode('UTF-8')
        except:
            # reraise everything
            raise


class FileToTextMixin(object):
    """
    Interface for converting a PDF file into text format using pdftotext
    """

    def file_get_contents(self, url, max_pages=20):
        """
        Convenience method to download a PDF file and converting it to text.
        """
        if max_pages < 1:  # do not process if not at least one
            return

        tf = self.file_download(url)
        if tf is not None:
            return self.file_to_text(tf.name, max_pages)
        else:
            return []  # FIXME: should be something else ...

    def file_download(self, url):
        """
        Downloads a given url to a tempfile.
        """

        log.debug("Downloading %s", url)
        try:
            # GO has no wildcard domain for SSL
            r = self.http_session.get(url, verify=False, timeout=5)
            tf = tempfile.NamedTemporaryFile()
            tf.write(r.content)
            tf.seek(0)
            return tf
        except HTTPError as e:
            log.info("Something went wrong downloading %s", url)
        except Exception as e:
            log.warning("Some other exception %s", url)

    def file_to_text(self, path, max_pages=20):
        """
        Method to convert a given PDF file into text file using a subprocess
        """

        return file_parser(path, max_pages)
