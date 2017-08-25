from ocd_backend.models import owl


class AudioObject(owl.Thing):
    pass


class CreativeWork(owl.Thing):
    pass


class Event(owl.Thing):
    endDate = 'schema:endDate'
    startDate = 'schema:startDate'


class EventStatusType(owl.Thing):
    pass


class ImageObject(owl.Thing):
    contentUrl = 'schema:contentUrl'
    isBasedOn = 'schema:isBasedOn'
    fileFormat = 'schema:fileFormat'
    contentSize = 'schema:contentSize'
    encodingFormat = 'schema:encodingFormat'
    exifData = 'schema:exifData'
    width = 'schema:width'
    height = 'schema:height'


class PropertyValue(owl.Thing):
    name = 'schema:name'
    value = 'schema:value'


class Place(owl.Thing):
    pass


class VideoObject(owl.Thing):
    pass
