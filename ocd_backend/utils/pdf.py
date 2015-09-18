import os
import subprocess
import tempfile
import re
from cStringIO import StringIO

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

import requests

from ocd_backend import settings

def convert(fname, pages=None):
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)

    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)

    infile = file(fname, 'rb')
    for page in PDFPage.get_pages(infile, pagenums):
        interpreter.process_page(page)
    infile.close()
    converter.close()
    text = output.getvalue()
    output.close()
    return text


class PDFToTextMixin(object):
    """
    Interface for converting a PDF file into text format using pdftotext
    """

    def pdf_clean_text(self, text):
        return text
        # return re.sub(r'\s+', u' ', text)

    def pdf_get_contents(self, url):
        """
        Convenience method to download a PDF file and converting it to text.
        """
        tf = self.pdf_download(url)
        return self.pdf_to_text(tf.name)

    def pdf_download(self, url):
        """
        Downloads a given url to a tempfile.
        """

        print "Downloading %s" % (url,)
        r = self.http_session.get(url)
        r.raise_for_status()
        tf = tempfile.NamedTemporaryFile()
        tf.write(r.content)
        tf.seek(0)
        return tf

    def pdf_to_text(self, path):
        """
        Method to convert a given PDF file into text file using a subprocess
        """

        content = convert(path)

        return unicode(self.pdf_clean_text(content.decode('utf-8')))
