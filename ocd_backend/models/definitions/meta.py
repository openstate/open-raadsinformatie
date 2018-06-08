"""The classes in this ontology are defined by Argu BV. More details, current
definitions and information can be found here:
https://argu.co/ns/meta#

The purpose of this ontology is to define metadata information that describes
ie. when the data was processed, what collection it belongs to rights apply to
the data.
"""

import owl
from ocd_backend.models.definitions import Meta, Meeting
from ocd_backend.models.properties import StringProperty, DateTimeProperty


class Metadata(Meta, owl.Thing):
    # todo needs to be formalized in a ontology
    status = StringProperty(Meta, 'status')
    processing_started = DateTimeProperty(Meta, 'processingStarted')
    source_id = StringProperty(Meta, 'sourceId')
    collection = StringProperty(Meta, 'collection')
    rights = StringProperty(Meta, 'rights')

    skip_validation = True


class Run(Meta, owl.Thing):
    run_identifier = StringProperty(Meeting, 'runIdentifier')

    skip_validation = True
