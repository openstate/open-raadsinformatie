import owl
from .namespaces import SCHEMA, OPENGOV, COUNCIL
from owltology.property import StringProperty, DateTimeProperty, ArrayProperty, Relation, Instance


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
    EventCancelled = Instance(SCHEMA, 'EventCancelled')
    EventPostponed = Instance(SCHEMA, 'EventPostponed')
    EventRescheduled = Instance(SCHEMA, 'EventRescheduled')
    EventScheduled = Instance(SCHEMA, 'EventScheduled')
    EventCompleted = Instance(COUNCIL, 'EventCompleted')
    EventConfirmed = Instance(COUNCIL, 'EventConfirmed')
    EventInactive = Instance(COUNCIL, 'EventInactive')

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
