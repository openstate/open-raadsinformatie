"""The classes in this schema module are derived from and described by:
http://schema.org/
"""

import owl
from ocd_backend.models.definitions import Schema, Opengov, Dbo
from ocd_backend.models.model import Individual
from ocd_backend.models.properties import StringProperty, IntegerProperty, \
    DateTimeProperty, DateProperty, ArrayProperty, Relation


class MediaObject(Schema, owl.Thing):
    name = StringProperty(Schema, 'name')
    url = StringProperty(Schema, 'contentUrl')
    size_in_bytes = IntegerProperty(Schema, 'fileSize')
    file_type = StringProperty(Schema, 'fileType')
    additional_type = StringProperty(Schema, 'additionalType')
    creator = Relation(Schema, 'creator')
    content_type = StringProperty(Schema, 'encodingFormat')
    upload_date = DateProperty(Schema, 'uploadDate')
    caption = StringProperty(Schema, 'caption')
    embed_url = StringProperty(Schema, 'embedUrl')
    file_name = StringProperty(Dbo, 'filename')
    original_url = StringProperty(Schema, 'isBasedOn')
    text = StringProperty(Schema, 'text')

    enricher_task = 'file_to_text'


class AudioObject(Schema, owl.Thing):
    contentUrl = StringProperty(Schema, 'contentUrl')


class CreativeWork(Schema, owl.Thing):
    legislative_session = Relation(Opengov, 'legislativeSession')
    creator = Relation(Schema, 'creator')
    date_created = DateTimeProperty(Schema, 'dateCreated')
    name = StringProperty(Schema, 'name')
    organizer = Relation(Schema, 'organizer')
    text = StringProperty(Schema, 'text')


class Event(Schema, owl.Thing):
    end_date = DateTimeProperty(Schema, 'endDate')
    start_date = DateTimeProperty(Schema, 'startDate')


class ImageObject(Schema, owl.Thing):
    content_url = StringProperty(Schema, 'contentUrl')
    is_based_on = StringProperty(Schema, 'isBasedOn')
    file_format = StringProperty(Schema, 'fileFormat')
    content_size = StringProperty(Schema, 'contentSize')
    encoding_format = StringProperty(Schema, 'encodingFormat')
    exif_data = ArrayProperty(Schema, 'exifData')
    width = StringProperty(Schema, 'width')
    height = StringProperty(Schema, 'height')

    enricher_task = 'image_metadata'


class PropertyValue(Schema, owl.Thing):
    name = StringProperty(Schema, 'name')
    value = StringProperty(Schema, 'value')


class Place(Schema, owl.Thing):
    pass


class VideoObject(Schema, owl.Thing):
    content_url = StringProperty(Schema, 'contentUrl')


# EventStatusType Individuals
class EventCancelled(Schema, Individual):
    pass


class EventPostponed(Schema, Individual):
    pass


class EventRescheduled(Schema, Individual):
    pass


class EventScheduled(Schema, Individual):
    pass
