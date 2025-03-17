import sys
import os
from urllib import parse
from tempfile import NamedTemporaryFile

import requests

from ocd_backend.app import celery_app
from ocd_backend.enrichers import BaseEnricher
from ocd_backend.exceptions import SkipEnrichment
from ocd_backend.log import get_source_logger
from ocd_backend.settings import RESOLVER_BASE_URL, RETRY_MAX_RETRIES, OCR_VERSION
from ocd_backend.models.postgres_database import PostgresDatabase
from ocd_backend.models.serializers import PostgresSerializer
from ocd_backend.utils.file_parsing import file_parser, md_file_parser, md_file_parser_using_ocr, parse_result_is_empty, rewrite_problematic_pdfs
from ocd_backend.utils.http import HttpRequestSimple
from ocd_backend.utils.misc import strip_scheme
from ocd_backend.utils.ori_document import OriDocument

from ocd_backend.enrichers.text_enricher.tasks.void import VoidEnrichtmentTask
from ocd_backend.enrichers.text_enricher.tasks.theme_classifier import ThemeClassifier
from ocd_backend.enrichers.text_enricher.tasks.waaroverheid import WaarOverheidEnricher
from ocd_backend.utils.retry_utils import is_retryable_error, retry_task

log = get_source_logger('enricher')


class TextEnricher(BaseEnricher):
    """An enricher that is responsible for enriching external files containing
     text

    Items are fetched from the source and then passed on to a
    set of registered tasks that are responsible for the analysis.
    """

    #: The registry of available sub-tasks that are responsible for the
    #: analysis of media items.
    available_tasks = {
        # 'theme_classifier': ThemeClassifier,
        # 'waaroverheid': WaarOverheidEnricher,
        'theme_classifier': VoidEnrichtmentTask,
        'waaroverheid': VoidEnrichtmentTask,
    }

    def __init__(self):
        database = PostgresDatabase(serializer=PostgresSerializer)
        self.session = database.Session()

    def enrich_item(self, item, metadata):
        """Enriches the media objects referenced in a single item.

        First, a media item will be retrieved from the source, then the
        registered and configured tasks will run. In case fetching the
        item fails, enrichment of the media item will be skipped. In case
        a specific media enrichment task fails, only that task is
        skipped, which means that we move on to the next task.
        """

        try:
            identifier = strip_scheme(item.identifier_url)
        except AttributeError:
            raise Exception('No identifier_url for item: %s', item)

        item.url = '%s/%s' % (RESOLVER_BASE_URL, parse.quote(identifier))

        if not hasattr(item, 'text') or not item.text:
            resource = None
            try:
                resource = HttpRequestSimple().fetch(
                    item.original_url,
                    identifier
                )
            except requests.HTTPError as e:
                log.info(f"HTTPError occurred for fetch in enrich_item, error is {e}")
                # Notubiz seems to return a 400 if permission to access the url is denied
                # GO returns a 404 if document not found
                if e.response.status_code >= 400 and e.response.status_code <= 410:
                    raise SkipEnrichment(e)
                else:
                    raise
            except requests.exceptions.ConnectionError as e:
                log.info(f"ConnectionError occurred for fetch in enrich_item, error is {e}")
                if is_retryable_error(e):
                    raise
                else:
                    raise SkipEnrichment(e)
            except requests.exceptions.TooManyRedirects as e:
                log.info(f"TooManyRedirects occurred for fetch in enrich_item, error is {e}")
                # configuration error on supplier side, cannot do much here
            except requests.exceptions.MissingSchema as e:
                log.info(f"MissingSchema occurred for fetch in enrich_item, error is {e}")
                # sometimes a "/tmp/..." url is encountered
            except requests.exceptions.RetryError as e:
                log.info(f"RetryError occurred for fetch in enrich_item, error is {e}")
                if is_retryable_error(e):
                    raise
                else:
                    raise SkipEnrichment(e)
            except:
                log.info(f"Generic error occurred for fetch in enrich_item, error class is {sys.exc_info()[0]}, {sys.exc_info()[1]}")
                raise

            if resource is not None:
                item.content_type = resource.content_type
                item.size_in_bytes = resource.file_size

                # Make sure file_object is actually on the disk for pdf parsing
                # Pass delete=False, since we keep the file
                temporary_file = NamedTemporaryFile(delete=False)
                temporary_file.write(resource.read())
                temporary_file.close()

                if os.path.exists(temporary_file.name):
                    path = os.path.realpath(temporary_file.name)
                    item.text = file_parser(path, item.original_url, max_pages=100)

                    ocr_used = None
                    md_path = rewrite_problematic_pdfs(path, item.original_url)
                    item.md_text = md_file_parser(md_path, item.original_url)
                    if parse_result_is_empty(item.md_text):
                        log.info(f"Parse result is empty for {item.original_url}, now trying OCR")
                        item.md_text = md_file_parser_using_ocr(md_path, item.original_url)
                        ocr_used = OCR_VERSION

                    ori_document = OriDocument(path, item, ocr_used=ocr_used, metadata=metadata)
                    ori_document.store()

            if hasattr(item, 'text') and item.text:
                # Adding the same text again for Elastic nesting
                item.text_pages = [
                    {'text': text, 'page_number': i}
                    for i, text in enumerate(item.text, start=1)
                    if text
                ]

        enrich_tasks = item.enricher_task
        if isinstance(enrich_tasks, str):
            enrich_tasks = [item.enricher_task]

        # The enricher tasks will executed in specified order
        for task in enrich_tasks:
            self.available_tasks[task](self.source_definition).enrich_item(item, metadata)

        item.db.save(item)


@celery_app.task(bind=True, base=TextEnricher, max_retries=RETRY_MAX_RETRIES)
@retry_task
def text_enricher(self, *args, **kwargs):
    return self.start(*args, **kwargs)
