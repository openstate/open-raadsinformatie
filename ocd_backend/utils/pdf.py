import os
import subprocess
from StringIO import StringIO
import tempfile
import re

import requests

from ocd_backend import settings


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

        process = subprocess.Popen(
            [settings.PDF_TO_TEXT, "-layout", "-enc", "UTF-8", path, "-"],
            shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        content, err = process.communicate()[0:2]

        if err is not None:
            raise ValueError

        return self.pdf_clean_text(content.decode('utf-8'))
