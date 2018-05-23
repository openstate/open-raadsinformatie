import owl
from ..property import StringProperty, DateTimeProperty
from .namespaces import META, COUNCIL


class Metadata(owl.Thing):
    # todo needs to be formalized in a ontology
    status = StringProperty(META, 'status')
    processing_started = DateTimeProperty(META, 'processingStarted')
    source_id = StringProperty(META, 'sourceId')
    collection = StringProperty(META, 'collection')
    rights = StringProperty(META, 'rights')

    class Meta:
        namespace = META


class Run(owl.Thing):
    run_identifier = StringProperty(COUNCIL, 'runIdentifier')

    class Meta:
        namespace = META
        temporary = False
