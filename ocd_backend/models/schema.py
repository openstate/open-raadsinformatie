import owl
from .namespaces import SCHEMA
from owltology.property import Type, OnlyDate


class AudioObject(owl.Thing):
    NAMESPACE = SCHEMA


class CreativeWork(owl.Thing):
    NAMESPACE = SCHEMA


class Event(owl.Thing):
    NAMESPACE = SCHEMA
    _type = Type(SCHEMA)
    endDate = OnlyDate(SCHEMA, 'endDate')
    startDate = OnlyDate(SCHEMA, 'schema:startDate')


class EventStatusType(owl.Thing):
    NAMESPACE = SCHEMA


class ImageObject(owl.Thing):
    NAMESPACE = SCHEMA
    contentUrl = 'schema:contentUrl'
    isBasedOn = 'schema:isBasedOn'
    fileFormat = 'schema:fileFormat'
    contentSize = 'schema:contentSize'
    encodingFormat = 'schema:encodingFormat'
    exifData = 'schema:exifData'
    width = 'schema:width'
    height = 'schema:height'


class PropertyValue(owl.Thing):
    NAMESPACE = SCHEMA
    name = 'schema:name'
    value = 'schema:value'


class Place(owl.Thing):
    NAMESPACE = SCHEMA


class VideoObject(owl.Thing):
    NAMESPACE = SCHEMA
