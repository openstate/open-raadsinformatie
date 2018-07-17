"""The classes in this schema module are derived from and described by:
http://schema.org/
"""

import owl
from ocd_backend.models.definitions import SCHEMA, OPENGOV
from ocd_backend.models.model import Individual
from ocd_backend.models.properties import StringProperty, IntegerProperty, \
    DateTimeProperty, ArrayProperty, Relation


class MediaObject(owl.Thing):
    name = StringProperty(SCHEMA, 'name')
    url = StringProperty(SCHEMA, 'contentUrl')
    size_in_bytes = IntegerProperty(SCHEMA, 'fileSize')
    file_type = StringProperty(SCHEMA, 'fileType')
    additional_type = StringProperty(SCHEMA, 'additionalType')
    creator = Relation(SCHEMA, 'creator')
    content_type = StringProperty(SCHEMA, 'fileFormat')
    original_url = StringProperty(SCHEMA, 'isBasedOn')
    text = StringProperty(SCHEMA, 'text')

    class Meta:
        enricher_task = 'file_to_text'


class AudioObject(owl.Thing):
    contentUrl = StringProperty(SCHEMA, 'contentUrl')


class CreativeWork(owl.Thing):
    legislative_session = Relation(OPENGOV, 'legislativeSession')
    creator = Relation(SCHEMA, 'creator')
    date_created = DateTimeProperty(SCHEMA, 'dateCreated')
    name = StringProperty(SCHEMA, 'name')
    organizer = Relation(SCHEMA, 'organizer')
    text = StringProperty(SCHEMA, 'text')


class Event(owl.Thing):
    end_date = DateTimeProperty(SCHEMA, 'endDate')
    start_date = DateTimeProperty(SCHEMA, 'startDate')


class ImageObject(owl.Thing):
    content_url = StringProperty(SCHEMA, 'contentUrl')
    is_based_on = StringProperty(SCHEMA, 'isBasedOn')
    file_format = StringProperty(SCHEMA, 'fileFormat')
    content_size = StringProperty(SCHEMA, 'contentSize')
    encoding_format = StringProperty(SCHEMA, 'encodingFormat')
    exif_data = ArrayProperty(SCHEMA, 'exifData')
    width = StringProperty(SCHEMA, 'width')
    height = StringProperty(SCHEMA, 'height')

    class Meta:
        enricher_task = 'image_metadata'


class PropertyValue(owl.Thing):
    name = StringProperty(SCHEMA, 'name')
    value = StringProperty(SCHEMA, 'value')


class Place(owl.Thing):
    pass


class VideoObject(owl.Thing):
    content_url = StringProperty(SCHEMA, 'contentUrl')


# EventStatusType Individuals
class EventCancelled(Individual):
    pass


class EventPostponed(Individual):
    pass


class EventRescheduled(Individual):
    pass


class EventScheduled(Individual):
    pass
