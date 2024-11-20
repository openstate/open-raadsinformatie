import os
import json
from urllib import parse
from tempfile import NamedTemporaryFile

import requests

from ocd_backend.app import celery_app
from ocd_backend.enrichers import BaseEnricher
from ocd_backend.exceptions import SkipEnrichment
from ocd_backend.log import get_source_logger
from ocd_backend.settings import RESOLVER_BASE_URL, AUTORETRY_EXCEPTIONS
from ocd_backend.utils.file_parsing import file_parser
from ocd_backend.utils.http import HttpRequestSimple
from ocd_backend.utils.misc import strip_scheme

from ocd_backend.enrichers.text_enricher.tasks.void import VoidEnrichtmentTask
from ocd_backend.enrichers.text_enricher.tasks.ggm_motion_text import GegevensmagazijnMotionText
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
        # 'ggm_motion_text': GegevensmagazijnMotionText,
        # 'theme_classifier': ThemeClassifier,
        # 'waaroverheid': WaarOverheidEnricher,
        'ggm_motion_text': VoidEnrichtmentTask,
        'theme_classifier': VoidEnrichtmentTask,
        'waaroverheid': VoidEnrichtmentTask,
    }

    def enrich_item(self, item):
        """Enriches the media objects referenced in a single item.

        First, a media item will be retrieved from the source, than the
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
            try:
                resource = HttpRequestSimple().fetch(
                    item.original_url,
                    identifier
                )
            except (ConnectionError, requests.HTTPError) as e:
                raise SkipEnrichment(e)

            item.content_type = resource.content_type
            item.size_in_bytes = resource.file_size

            # Make sure file_object is actually on the disk for pdf parsing
            temporary_file = NamedTemporaryFile(delete=True)
            temporary_file.write(resource.read())
            temporary_file.seek(0, 0)

            if os.path.exists(temporary_file.name):
                path = os.path.realpath(temporary_file.name)
                item.text = file_parser(path, max_pages=100)

            temporary_file.close()

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
            self.available_tasks[task](self.source_definition).enrich_item(item)

        item.db.save(item)


@celery_app.task(bind=True, base=TextEnricher, autoretry_for=AUTORETRY_EXCEPTIONS, retry_backoff=True)
def text_enricher(self, *args, **kwargs):
    return self.start(*args, **kwargs)
