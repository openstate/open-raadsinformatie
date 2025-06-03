import json

from ocd_backend import settings
from ocd_backend.app import celery_app
from elasticsearch import TransportError
from ocd_backend.es import elasticsearch
from ocd_backend.exceptions import ConfigurationError
from ocd_backend.loaders import BaseLoader
from ocd_backend.log import get_source_logger
from ocd_backend.models.serializers import JsonLDSerializer
from ocd_backend.utils.misc import json_encoder
from ocd_backend.settings import AUTORETRY_EXCEPTIONS, RETRY_MAX_RETRIES, AUTORETRY_RETRY_BACKOFF, AUTORETRY_RETRY_BACKOFF_MAX

log = get_source_logger('elasticsearch_loader')


class ElasticsearchBaseLoader(BaseLoader):
    def start(self, *args, **kwargs):
        self.index_name = kwargs.get('new_index_name')

        if not self.index_name:
            raise ConfigurationError('The name of the index is not provided')

        return super(ElasticsearchBaseLoader, self).start(*args, **kwargs)

    def load_item(self, doc):
        if doc is None:
            log.debug(f'{self.__name__} doc==None received, probably due to a non-retryable error in enricher')
            return

        log_identifiers = []

        # Recursively index associated models like attachments
        for model in doc.traverse():
            self.add_metadata(model, doc == model)
            model_body = json_encoder.encode(JsonLDSerializer(loader_class=self).serialize(model))

            try:
                self.process(model, model_body)
                log_identifiers.append(model.get_short_identifier())
            except TransportError as e:
                log.info(f"TransportError when uploading {model.get_short_identifier()} to ES: {e}")
                log.info(f"Length model_body: {len(model_body)}")
                if e.status_code == 413:
                    # Body is too large (> 100MB). This typically happens when pdf consists mainly of
                    # complicated kadaster maps; the output contains mostly spaces and newlines and can be ignored
                    pass
                else:
                    raise e
            except Exception as e:
                log.info(f"ERROR when uploading {model.get_short_identifier()} to ES: {e}")
                log.info(f"Length model_body: {len(model_body)}")
                raise e

        log.debug(f'{self.__name__} indexing document id: {", ".join(log_identifiers)}')

    def process(self, model, model_body):
        raise NotImplementedError


class ElasticsearchLoader(ElasticsearchBaseLoader):
    """Indexes items into Elasticsearch."""

    def process(self, model, model_body):
        # Index document into new index
        elasticsearch.index(
            index=self.index_name,
            body=model_body,
            id=model.get_short_identifier()
        )


class ElasticsearchUpdateOnlyLoader(ElasticsearchBaseLoader):
    """
    Updates elasticsearch items using the update method. Use with caution.
    """

    def process(self, model, model_body):
        elasticsearch.update(
            id=model.get_short_identifier(),
            index=self.index_name,
            body={'doc': json.loads(model_body)},
        )


class ElasticsearchUpsertLoader(ElasticsearchBaseLoader):
    """
    Updates elasticsearch items using the update method.
    """

    def process(self, model, model_body):
        elasticsearch.update(
            id=model.get_short_identifier(),
            index=self.index_name,
            body={
                'doc': json.loads(model_body),
                'doc_as_upsert': True,
            },
        )


@celery_app.task(bind=True, base=ElasticsearchLoader, autoretry_for=AUTORETRY_EXCEPTIONS,
                 retry_backoff=AUTORETRY_RETRY_BACKOFF, max_retries=RETRY_MAX_RETRIES, retry_backoff_max=AUTORETRY_RETRY_BACKOFF_MAX)
def elasticsearch_loader(self, *args, **kwargs):
    return self.start(*args, **kwargs)


@celery_app.task(bind=True, base=ElasticsearchUpdateOnlyLoader, autoretry_for=AUTORETRY_EXCEPTIONS,
                 retry_backoff=AUTORETRY_RETRY_BACKOFF, max_retries=RETRY_MAX_RETRIES, retry_backoff_max=AUTORETRY_RETRY_BACKOFF_MAX)
def elasticsearch_update_only_loader(self, *args, **kwargs):
    return self.start(*args, **kwargs)


@celery_app.task(bind=True, base=ElasticsearchUpsertLoader, autoretry_for=AUTORETRY_EXCEPTIONS,
                 retry_backoff=AUTORETRY_RETRY_BACKOFF, max_retries=RETRY_MAX_RETRIES, retry_backoff_max=AUTORETRY_RETRY_BACKOFF_MAX)
def elasticsearch_upsert_loader(self, *args, **kwargs):
    return self.start(*args, **kwargs)
