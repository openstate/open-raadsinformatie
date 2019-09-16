import magic
import pdftotext

from ocd_backend.log import get_source_logger

log = get_source_logger('file_parser')


def file_parser(fname, max_pages=None):
    if magic.from_file(fname, mime=True) == 'application/pdf':
        with open(fname, "rb") as f:
            result_pages = []
            for i, page in enumerate(pdftotext.PDF(f), start=1):
                result_pages.append(page)

                if max_pages and i > max_pages:  # break after x pages
                    break

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
