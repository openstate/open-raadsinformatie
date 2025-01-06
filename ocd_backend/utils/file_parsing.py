import magic
import pdftotext
import pymupdf
import pymupdf4llm

from ocd_backend.log import get_source_logger

log = get_source_logger('file_parser')


def file_parser(fname, max_pages=None):
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
                log.warning(str(e))

            log.debug("Processed %i pages" % i)
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

def md_file_parser(fname, max_pages=None):
    if magic.from_file(fname, mime=True) == 'application/pdf':
        doc=pymupdf.open(fname)
        hdr=pymupdf4llm.IdentifyHeaders(doc)
        md_chunks = pymupdf4llm.to_markdown(fname, hdr_info=hdr, page_chunks=True, show_progress=False)
        md_text = [chunk['text'] for chunk in md_chunks]

        return md_text
    else:
        pass

