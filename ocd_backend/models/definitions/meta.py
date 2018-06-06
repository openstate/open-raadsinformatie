"""The classes in this ontology are defined by Argu BV. More details, current
definitions and information can be found here:
https://argu.co/ns/meta#

The purpose of this ontology is to define metadata information that describes
ie. when the data was processed, what collection it belongs to rights apply to
the data.
"""

import owl
from ..property import StringProperty, DateTimeProperty
from . import META, MEETING


class Metadata(owl.Thing):
    # todo needs to be formalized in a ontology
    status = StringProperty(META, 'status')
    processing_started = DateTimeProperty(META, 'processingStarted')
    source_id = StringProperty(META, 'sourceId')
    collection = StringProperty(META, 'collection')
    rights = StringProperty(META, 'rights')

    class Meta:
        skip_validation = True


class Run(owl.Thing):
    run_identifier = StringProperty(MEETING, 'runIdentifier')

    class Meta:
        skip_validation = True
