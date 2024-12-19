import sys
import os
import json
from urllib import parse
from tempfile import NamedTemporaryFile

import requests

from ocd_backend.app import celery_app
from ocd_backend.enrichers import BaseEnricher
from ocd_backend.exceptions import SkipEnrichment
from ocd_backend.log import get_source_logger
from ocd_backend.models.postgres_database import PostgresDatabase
from ocd_backend.models.serializers import PostgresSerializer
from ocd_backend.settings import RESOLVER_BASE_URL, AUTORETRY_EXCEPTIONS, AUTORETRY_MAX_RETRIES, AUTORETRY_RETRY_BACKOFF, AUTORETRY_RETRY_BACKOFF_MAX
from ocd_backend.utils.file_parsing import file_parser
from ocd_backend.utils.http import HttpRequestSimple
from ocd_backend.utils.misc import strip_scheme
from ocd_backend.utils.document_storage import DocumentStorage
from ocd_backend.models.postgres_models import StoredDocument
import magic

from ocd_backend.enrichers.text_enricher.tasks.void import VoidEnrichtmentTask
from ocd_backend.enrichers.text_enricher.tasks.theme_classifier import ThemeClassifier
from ocd_backend.enrichers.text_enricher.tasks.waaroverheid import WaarOverheidEnricher

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

    def enrich_item(self, item):
        """Enriches the media objects referenced in a single item.

        First, a media item will be retrieved from the source, than the
        registered and configured tasks will run. In case fetching the
        item fails, enrichment of the media item will be skipped. In case
        a specific media enrichment task fails, only that task is
        skipped, which means that we move on to the next task.
        """

        log.info(f"RVD item in enrich_item is {item.get_short_identifier()} {vars(item)}")
        try:
            identifier = strip_scheme(item.identifier_url)
        except AttributeError:
            raise Exception('No identifier_url for item: %s', item)

        item.url = '%s/%s' % (RESOLVER_BASE_URL, parse.quote(identifier))

        if not hasattr(item, 'text') or not item.text:
            try:
                resource = HttpRequestSimple().fetch(
                    item.original_url,
                    identifier
                )
            except (requests.HTTPError) as e:
                log.info(f"HTTPError occurred for fetch in enrich_item, error class is {e.__class__.__name__}")
                # Notubiz seems to return a 400 if permission to access the url is denied
                if e.response.status_code == 400:
                    raise SkipEnrichment(e)
                else:
                    raise
            except:
                log.info(f"Generic error occurred for fetch in enrich_item, error class is {sys.exc_info()[0]}, {sys.exc_info()[1]}")
                raise

            item.content_type = resource.content_type
            item.size_in_bytes = resource.file_size

            # Make sure file_object is actually on the disk for pdf parsing
            temporary_file = NamedTemporaryFile(delete=True)
            temporary_file.write(resource.read())
            temporary_file.seek(0, 0)

            if os.path.exists(temporary_file.name):
                path = os.path.realpath(temporary_file.name)
                item.text = file_parser(path, max_pages=100)

                document_storage = DocumentStorage(path, item.file_name, item.size_in_bytes, item.get_short_identifier())
                # item.text_md = DocumentStorage.text_md()
                # Store PDF for potential later re-use (in db and on disk)
                # Notubiz send last_modified which is stored in date_modified (so NOT in last_discussed_at)
                # Notubiz also sends version and file_size
                # ibabs does not send a date, id
                # ibabs does send FileSize, Id 

                content_type = magic.from_file(path, mime=True)

                stored_document = StoredDocument(resource_ori_id=item.get_short_identifier(), content_type=content_type, size = item.size_in_bytes)
                self.session.add(stored_document)
                self.session.commit()
                self.session.flush()
                log.info(f"stored_document: {stored_document.id}, {vars(stored_document)}")
                    
                asdfasfds()
                DocumentStorage.full_name(434, item.get_short_identifier())

            temporary_file.close()

            if hasattr(item, 'text') and item.text:
                # Adding the same text again for Elastic nesting
                item.text_pages = [
                    {'text': text, 'page_number': i}
                    for i, text in enumerate(item.text, start=1)
                    if text
                ]
                # Save in stored_documents table

        enrich_tasks = item.enricher_task
        if isinstance(enrich_tasks, str):
            enrich_tasks = [item.enricher_task]

        # The enricher tasks will executed in specified order
        for task in enrich_tasks:
            self.available_tasks[task](self.source_definition).enrich_item(item)

        item.db.save(item)


@celery_app.task(bind=True, base=TextEnricher, autoretry_for=AUTORETRY_EXCEPTIONS,
                 retry_backoff=AUTORETRY_RETRY_BACKOFF, max_retries=AUTORETRY_MAX_RETRIES, retry_backoff_max=AUTORETRY_RETRY_BACKOFF_MAX)
def text_enricher(self, *args, **kwargs):
    return self.start(*args, **kwargs)
