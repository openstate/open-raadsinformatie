import os
import re
import sys
from tempfile import gettempdir
import uuid

import magic
import pdftotext
import pymupdf
from pymupdf import mupdf
import pymupdf4llm

from ocd_backend.log import get_source_logger

log = get_source_logger('file_parser')
pymupdf.TOOLS.mupdf_display_errors(False)
pymupdf.TOOLS.mupdf_display_warnings(False)

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
                if 'poppler error creating document' in str(e) or 'poppler error creating page' in str(e) or \
                    'failed to unlock document' in str(e):
                    pass # unreadable pdf
                else:
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

# Some PDFs were found to have 30k image objects in the dict on a single page (not real images).
# Due to inefficient looping these files are impossible to process (takes days).
# The quickest solution is to rewrite those files first using pymupdf.
def rewrite_problematic_pdfs(fname, new_name, original_url):
    if magic.from_file(fname, mime=True) != 'application/pdf':
        return fname

    try:
        rewrite = False
        with pymupdf.open(fname) as doc: 
            for page in doc.pages():
                number_of_images = len(page.get_images())
                if number_of_images > 100:
                    log.info(f"PDF for {original_url} contains many image objects on a page ({number_of_images}), will be rewritten")
                    rewrite = True
                    break
        if not rewrite:
            return fname
    except:
        log.info(f"Generic error occurred when checking number of pages in pdf for {original_url}, error class is {sys.exc_info()[0]}, {sys.exc_info()[1]}")
        return

    if pdf_black_listed(original_url):
        return
            
    try:
        with pymupdf.open(fname) as doc:
            doc.save(new_name, garbage=3, clean=True)

        # Sometimes rewriting the PDF does not significantly reduce the number of images, potentially leading to
        # millions of objects in `img_bboxes` in pymupdf and hanging PDF conversions.
        # Prevent this by now simply deleting those pages with too many images
        with pymupdf.open(new_name) as doc: 
            number_of_images_all_pages = {}
            for index, page in enumerate(doc.pages()):
                number_of_images = len(page.get_images())
                if number_of_images > 100:
                    number_of_images_all_pages[index] = number_of_images
            if len(number_of_images_all_pages) > 0:
                log.info(f"Rewritten PDF for {original_url} still contains many image objects on a page ({number_of_images_all_pages}), deleting those pages now")
                sorted_keys = sorted(number_of_images_all_pages.keys(), reverse=True)
                for page_no in sorted_keys:
                    doc.delete_page(page_no)
                if doc.page_count == 0:
                    new_name = None
                else:
                    doc.saveIncr()
        return new_name
    except:
        log.info(f"Generic error occurred when rewriting pdf for {original_url}, error class is {sys.exc_info()[0]}, {sys.exc_info()[1]}")
    
    return

# Some PDFs were found to have tens of thousands of bboxes.
# Due to inefficient looping these files are impossible to process (takes days).
# If a pdf has a page with many bboxes force usage of OCR
def force_ocr(fname, original_url):
    # Large files impossible to process otherwise, seems to be caused by lots of strike-through text
    force_ocr_for = [
        'https://api.notubiz.nl/document/15349436/2'
    ]
    if original_url in force_ocr_for:
        return  True

    textflags = ( # definition taken from pymupdf4llm
        0
        | mupdf.FZ_STEXT_CLIP
        | mupdf.FZ_STEXT_ACCURATE_BBOXES
        # | mupdf.FZ_STEXT_IGNORE_ACTUALTEXT
        | 32768  # mupdf.FZ_STEXT_COLLECT_STYLES
    )

    try:
        with pymupdf.open(fname) as doc: 
            for page in doc.pages():
                textpage = page.get_textpage(flags=textflags, clip=page.rect)
                blocks = textpage.extractDICT()["blocks"]
                if len(blocks) > 150:
                    return True
    except:
        log.info(f"Generic error occurred when getting number of bboxes in pdf for {original_url}, error class is {sys.exc_info()[0]}, {sys.exc_info()[1]}")

    return False

def pdf_black_listed(original_url):
    # Some pdfs lead to a Celery `WorkerLostError: Worker exited prematurely`, it is unknown why, avoid them.
    worker_lost_pdfs = [
        'https://api1.ibabs.eu/publicdownload.aspx?site=Assen&id=1f8f7469-6bad-4ccf-9a30-387b759210a2'
    ]

    # Some pdfs take days of processing (until killed), avoid them.
    indefinite_processing_time_pdfs = [
        'https://raad.sliedrecht.nl/api/v1/meetings/940/documents/11924',
        'https://raad.sliedrecht.nl/api/v1/meetings/943/documents/11924'
    ]

    if original_url in worker_lost_pdfs or original_url in indefinite_processing_time_pdfs:
        return True
    else:
        return False

def make_temp_pdf_fname():
    name = os.path.join(gettempdir(), str(uuid.uuid1()))
    return f"{name}.pdf"

def md_file_parser(fname, original_url):
    if magic.from_file(fname, mime=True) != 'application/pdf':
        return

    try:
        with pymupdf.open(fname) as doc:
            hdr=pymupdf4llm.IdentifyHeaders(doc)
            try:
                # Without the image_size_limit=0.1 a page with many very small images cannot be processed due to O(n*n) complexity
                md_chunks = pymupdf4llm.to_markdown(fname, hdr_info=hdr, page_chunks=True, show_progress=False, image_size_limit=0.1)
            except ValueError as e:
                log.info(f'ValueError when calling pymupdf4llm.to_markdown for {original_url}, reason: {e}')
                return ""
            except IndexError as e:
                log.info(f'IndexError when calling pymupdf4llm.to_markdown for {original_url}, reason: {e}')
                return ""

            md_text = [chunk['text'] for chunk in md_chunks]

            log.debug(f"Processed {len(md_text)} pages to markdown for {original_url}")

            return md_text
    except:
        log.info(f"Generic error occurred when opening pdf in md_file_parser for {original_url}, error class is {sys.exc_info()[0]}, {sys.exc_info()[1]}")

    return ""

# When OCR is applied, font information is not retrieved so output is plain text instead of markdown.
# Therefore we use page.get_text from pymupdf instead of using pymupdf4llm.
# full=False was found to give ok results. No improvement was found with full=True and dpi values of
# 150, 200, 300 and 500.
def md_file_parser_using_ocr(fname, original_url):
    if magic.from_file(fname, mime=True) != 'application/pdf':
        return

    try:
        with pymupdf.open(fname) as doc:
            md_text = []
            for page in doc:
                try:
                    text_page = page.get_textpage_ocr(flags=pymupdf.TEXTFLAGS_SEARCH, language='nld', full=False)
                    text = page.get_text(textpage=text_page)
                    md_text.append(text)
                except ValueError as e:
                    log.info(f'ValueError when calling page.get_textpage_ocr for {original_url}, reason: {e}')
                    # just skip page
            log.debug(f"Processed {len(md_text)} pages using OCR for {original_url}")

            return md_text
    except:
        log.info(f"Generic error occurred when opening pdf in md_file_parser_using_ocr for {original_url}, error class is {sys.exc_info()[0]}, {sys.exc_info()[1]}")
        return []

def parse_result_is_empty(md_text):
    if md_text is None:
        return False
    
    # If at least a single digit or letter is present on a page we consider it not empty  
    for page in md_text:
        if re.search("[a-zA-Z0-9]", page):
            return False
        
    return True