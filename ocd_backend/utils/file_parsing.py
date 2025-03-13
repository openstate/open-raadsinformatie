import re

import magic
import pdftotext
import pymupdf
import pymupdf4llm

from ocd_backend.log import get_source_logger

log = get_source_logger('file_parser')

def file_parser(fname, original_url, max_pages=None):
    if magic.from_file(fname, mime=True) == 'application/pdf':
        with open(fname, "rb") as f:
            result_pages = []
            i = 0
            try:
                for i, page in enumerate(pdftotext.PDF(f), start=1):
                    result_pages.append(page)

                    if max_pages and i >= max_pages:  # break after x pages
                        break
            except pdftotext.Error as e:
                log.warning(f"Error from pdftotext for {original_url}: {e}")
                raise e

            log.debug(f"Processed {i} pages to text for {original_url}")
            return result_pages
    else:
        # This code path is disabled until the Tika service is fixed (see issue 178)

        # try:
        #     content = parser.from_file(fname)['content']
        #     return (content or '').encode('UTF-8')
        # except:
        #     # reraise everything
        #     raise
        pass

def md_file_parser(fname, original_url):
    if magic.from_file(fname, mime=True) == 'application/pdf':
        doc=pymupdf.open(fname)
        hdr=pymupdf4llm.IdentifyHeaders(doc)
        md_chunks = pymupdf4llm.to_markdown(fname, hdr_info=hdr, page_chunks=True, show_progress=False)
        md_text = [chunk['text'] for chunk in md_chunks]

        log.debug(f"Processed {len(md_text)} pages to markdown for {original_url}")

        return md_text
    else:
        pass

# When OCR is applied, font information is not retrieved so output is plain text instead of markdown.
# Therefore we use page.get_text from pymupdf instead of using pymupdf4llm.
# full=False was found to give ok results. No improvement was found with full=True and dpi values of
# 150, 200, 300 and 500.
def md_file_parser_using_ocr(fname, original_url):
    if magic.from_file(fname, mime=True) == 'application/pdf':
        doc=pymupdf.open(fname)

        md_text = []
        for page in doc:
            text_page = page.get_textpage_ocr(flags=pymupdf.TEXTFLAGS_SEARCH, language='nld', full=False)
            text = page.get_text(textpage=text_page)
            md_text.append(text)

        log.debug(f"Processed {len(md_text)} pages using OCR for {original_url}")

        return md_text
    else:
        pass

def parse_result_is_empty(md_text):
    if md_text is None:
        return False
    
    # If at least a single digit or letter is present on a page we consider it not empty  
    for page in md_text:
        if re.search("[a-zA-Z0-9]", page):
            return False
        
    return True