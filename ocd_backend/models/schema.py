import owl
from .namespaces import SCHEMA, OPENGOV
from owltology.property import StringProperty, DateTimeProperty, ArrayProperty, Relation


class AudioObject(owl.Thing):
    contentUrl = StringProperty(SCHEMA, 'contentUrl')

    class Meta:
        namespace = SCHEMA


class CreativeWork(owl.Thing):
    legislative_session = Relation(OPENGOV, 'legislativeSession')
    creator = Relation(SCHEMA, 'creator')
    date_created = DateTimeProperty(SCHEMA, 'dateCreated')
    name = StringProperty(SCHEMA, 'name')
    organizer = Relation(SCHEMA, 'organizer')
    text = StringProperty(SCHEMA, 'text')

    class Meta:
        namespace = SCHEMA


class Event(owl.Thing):
    end_date = DateTimeProperty(SCHEMA, 'endDate')
    start_date = DateTimeProperty(SCHEMA, 'startDate')

    class Meta:
        namespace = SCHEMA


class EventStatusType(owl.Thing):
    # Instances
    EventCancelled = 'schema:EventCancelled'
    EventPostponed = 'schema:EventPostponed'
    EventRescheduled = 'schema:EventRescheduled'
    EventScheduled = 'schema:EventScheduled'
    EventCompleted = 'council:EventCompleted'
    EventConfirmed = 'council:EventConfirmed'
    EventInactive = 'council:EventInactive'

    class Meta:
        namespace = SCHEMA


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
        namespace = SCHEMA
        enricher_task = 'image_metadata'


class PropertyValue(owl.Thing):
    name = StringProperty(SCHEMA, 'name')
    value = StringProperty(SCHEMA, 'value')

    class Meta:
        namespace = SCHEMA


class Place(owl.Thing):
    class Meta:
        namespace = SCHEMA


class VideoObject(owl.Thing):
    content_url = StringProperty(SCHEMA, 'contentUrl')

    class Meta:
        namespace = SCHEMA
