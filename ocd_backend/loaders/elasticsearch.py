import simplejson as json

from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.es import elasticsearch
from ocd_backend.exceptions import ConfigurationError
from ocd_backend.loaders import BaseLoader
from ocd_backend.log import get_source_logger
from ocd_backend.models.serializers import JsonLDSerializer
from ocd_backend.utils.misc import json_encoder

log = get_source_logger('elasticsearch_loader')


class ElasticsearchBaseLoader(BaseLoader):
    def start(self, *args, **kwargs):
        self.index_name = kwargs.get('new_index_name')

        if not self.index_name:
            raise ConfigurationError('The name of the index is not provided')

        return super(ElasticsearchBaseLoader, self).start(*args, **kwargs)

    def load_item(self, doc):
        log_identifiers = []

        # Recursively index associated models like attachments
        for model in doc.traverse():
            self.add_metadata(model, doc == model)
            model_body = json_encoder.encode(JsonLDSerializer(loader_class=self).serialize(model))

            self.process(model, model_body)
            log_identifiers.append(model.get_short_identifier())

        log.debug('%s indexing document id: %s' % (self.__name__, ', '.join(log_identifiers)))

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


@celery_app.task(bind=True, base=ElasticsearchLoader, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def elasticsearch_loader(self, *args, **kwargs):
    return self.start(*args, **kwargs)


@celery_app.task(bind=True, base=ElasticsearchUpdateOnlyLoader, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def elasticsearch_update_only_loader(self, *args, **kwargs):
    return self.start(*args, **kwargs)


@celery_app.task(bind=True, base=ElasticsearchUpsertLoader, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def elasticsearch_upsert_loader(self, *args, **kwargs):
    return self.start(*args, **kwargs)
