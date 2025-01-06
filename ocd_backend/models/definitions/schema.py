"""The classes in this schema module are derived from and described by:
http://schema.org/
"""

from ocd_backend.models.definitions import owl
from ocd_backend.models.definitions import Schema, Opengov, Dbo, Dcterms, Meeting as MeetingNS, Cbs
from ocd_backend.models.properties import StringProperty, URLProperty, IntegerProperty, \
    DateTimeProperty, DateProperty, ArrayProperty, JsonProperty, Relation
from ocd_backend.models.misc import Uri

class MediaObject(Schema, owl.Thing):
    name = StringProperty(Schema, 'name')
    url = URLProperty(Schema, 'contentUrl')
    size_in_bytes = IntegerProperty(Schema, 'fileSize')
    file_type = StringProperty(Schema, 'fileType')
    additional_type = StringProperty(Schema, 'additionalType')
    creator = Relation(Schema, 'creator')
    content_type = StringProperty(Schema, 'encodingFormat')
    upload_date = DateProperty(Schema, 'uploadDate')
    caption = StringProperty(Schema, 'caption')
    embed_url = StringProperty(Schema, 'embedUrl')
    file_name = StringProperty(Dbo, 'filename')
    date_modified = DateTimeProperty(Schema, 'dateModified')
    original_url = URLProperty(Schema, 'isBasedOn')
    text = ArrayProperty(Schema, 'text')
    md_text = ArrayProperty(Schema, 'text')
    enriched_text = ArrayProperty(MeetingNS, 'enrichedText')
    text_pages = JsonProperty(MeetingNS, 'textPages')
    is_referenced_by = Relation(Dcterms, 'isReferencedBy')
    last_discussed_at = DateTimeProperty(MeetingNS, 'lastDiscussedAt')
    tags = JsonProperty(MeetingNS, 'tags')
    neighborhood_polygons = JsonProperty(MeetingNS, 'neighborhood_polygons')
    geometry = JsonProperty(MeetingNS, 'geometry')
    districts = ArrayProperty(Cbs, 'Wijk')
    neighborhoods = ArrayProperty(Cbs, 'Buurt')

    enricher_task = ['theme_classifier', 'waaroverheid']


class AudioObject(Schema, owl.Thing):
    contentUrl = URLProperty(Schema, 'contentUrl')


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
    last_discussed_at = DateTimeProperty(MeetingNS, 'lastDiscussedAt')


class ImageObject(Schema, owl.Thing):
    content_url = URLProperty(Schema, 'contentUrl')
    is_based_on = URLProperty(Schema, 'isBasedOn')
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
    content_url = URLProperty(Schema, 'contentUrl')


EventScheduled = Uri(Schema, "EventScheduled")
EventRescheduled = Uri(Schema, "EventRescheduled")
EventCancelled = Uri(Schema, "EventCancelled")
EventPostponed = Uri(Schema, "EventPostponed")
