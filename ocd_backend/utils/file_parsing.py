import tempfile
import magic
from urllib2 import HTTPError
from OpenSSL.SSL import ZeroReturnError

import pdfparser.poppler as pdf
import tika.parser as parser


def file_parser(fname, pages=None):
    if magic.from_file(fname, mime=True) == 'application/pdf':
        try:
            text_array = []
            d = pdf.Document(fname)
            for i, p in enumerate(d, start=1):
                for f in p:
                    for b in f:
                        for l in b:
                            text_array.append(l.text.encode('UTF-8'))

                if i == pages:  # break after x pages
                    break

            print "Processed %i pages" % (i)
            return '\n'.join(text_array)
        except Exception as e:
            print "PDF Parser Exception: ", e
    else:
        try:
            content = parser.from_file(fname)['content']
            return (content or '').encode('UTF-8')
        except Exception as e:
            print "File Parser Exception: ", e


class FileToTextMixin(object):
    """
    Interface for converting a PDF file into text format using pdftotext
    """

    def file_clean_text(self, text):
        return text
        # return re.sub(r'\s+', u' ', text)

    def file_get_contents(self, url, max_pages=20):
        """
        Convenience method to download a PDF file and converting it to text.
        """
        tf = self.file_download(url)
        if tf is not None:
            return self.file_to_text(tf.name, max_pages)
        else:
            return u'' # FIXME: should be something else ...

    def file_download(self, url):
        """
        Downloads a given url to a tempfile.
        """

        print "Downloading %s" % (url,)
        try:
            # GO has no wildcard domain for SSL
            r = self.http_session.get(url, verify=False)
            tf = tempfile.NamedTemporaryFile()
            tf.write(r.content)
            tf.seek(0)
            return tf
        except HTTPError as e:
            print "Something went wrong downloading %s" % (url,)
        except ZeroReturnError as e:
            print "SSL Zero return error %s" % (url,)
        except Exception as e:
            print "Some other exception %s" % (url,)

    def file_to_text(self, path, max_pages=20):
        """
        Method to convert a given PDF file into text file using a subprocess
        """


        content = file_parser(path, max_pages)
        text = self.file_clean_text(content.decode('utf-8'))
        return unicode(text)
