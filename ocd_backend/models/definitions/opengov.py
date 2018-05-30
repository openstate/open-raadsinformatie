import govid
import owl
import schema
from ..property import StringProperty, IntegerProperty, DateTimeProperty, ArrayProperty, Relation, InlineRelation, Instance
from .namespaces import OPENGOV, SCHEMA, COUNCIL, DCTERMS, NCAL, RDF, RDFS, SKOS, BIBFRAME


class Event(schema.Event):
    agenda = Relation(COUNCIL, 'agenda')
    attachment = InlineRelation(COUNCIL, 'attachment')
    classification = ArrayProperty(NCAL, 'categories')  # todo fix with popolo
    motion = Relation(OPENGOV, 'motion')
    attendee = Relation(SCHEMA, 'attendee')
    audio = Relation(SCHEMA, 'audio')
    description = StringProperty(SCHEMA, 'description')
    status = Instance(SCHEMA, 'eventStatus')
    location = StringProperty(SCHEMA, 'location')
    name = StringProperty(SCHEMA, 'name', required=True)
    organization = Relation(SCHEMA, 'organizer')
    committee = Relation(COUNCIL, 'committee')
    parent = Relation(SCHEMA, 'superEvent')
    chair = StringProperty(COUNCIL, 'chair')
    absentee = Relation(SCHEMA, 'absentee')
    invitee = Relation(SCHEMA, 'invitee')

    ggm_vrsnummer = govid.ggm_vrsnummer
    ggm_nummer = govid.ggm_nummer
    ggm_volgnummer = govid.ggm_volgnummer

    class Meta:
        namespace = OPENGOV


class Motion(owl.Thing):
    attachment = InlineRelation(SCHEMA, 'attachment')
    legislative_session = StringProperty(OPENGOV, 'legislativeSession')
    requirement = StringProperty(OPENGOV, 'requirement')
    classification = StringProperty(SCHEMA, 'additionalType')
    creator = Relation(SCHEMA, 'creator')
    cocreator = Relation(COUNCIL, 'cocreator')
    date = DateTimeProperty(SCHEMA, 'dateSubmitted')
    name = StringProperty(SCHEMA, 'name')
    organization = Relation(SCHEMA, 'publisher')
    text = StringProperty(SCHEMA, 'text')
    vote_events = Relation(OPENGOV, 'voteEvent')

    ggm_vrsnummer = govid.ggm_vrsnummer
    ggm_nummer = govid.ggm_nummer
    ggm_volgnummer = govid.ggm_volgnummer

    class Meta:
        namespace = OPENGOV


class VoteEvent(schema.Event):
    classification = ArrayProperty(NCAL, 'categories')
    created_at = DateTimeProperty(DCTERMS, 'created')
    updated_at = DateTimeProperty(DCTERMS, 'modified')
    motion = Relation(OPENGOV, 'motion')
    result = StringProperty(OPENGOV, 'result')
    organization = Relation(SCHEMA, 'organizer')
    legislative_session = Relation(SCHEMA, 'superEvent')
    votes = Relation(OPENGOV, 'vote')
    counts = Relation(OPENGOV, 'count')

    class Meta:
        namespace = OPENGOV


class Speech(owl.Thing):
    attribution_text = StringProperty(OPENGOV, 'attributionText')
    audience = Relation(DCTERMS, 'audience')
    event = Relation(BIBFRAME, 'event')
    role = Relation(OPENGOV, 'role')
    audio = Relation(SCHEMA, 'audio')
    creator = Relation(SCHEMA, 'creator')
    end_date = DateTimeProperty(SCHEMA, 'endDate')
    position = IntegerProperty(SCHEMA, 'position')
    start_date = DateTimeProperty(SCHEMA, 'startDate')
    text = StringProperty(SCHEMA, 'text')
    video = StringProperty(SCHEMA, 'video')

    class Meta:
        namespace = OPENGOV


class SpeechAnswer(Speech):
    pass


class SpeechNarrative(Speech):
    pass


class SpeechQuestion(Speech):
    pass


class SpeechScene(Speech):
    pass


class SpeechSummary(Speech):
    pass


class Count(owl.Thing):
    value = IntegerProperty(RDF, 'value')
    group = Relation(OPENGOV, 'group')

    class Meta:
        namespace = OPENGOV


class YesCount(Count):
    pass


class NoCount(Count):
    pass


class AbsentCount(Count):
    pass


class AbstainCount(Count):
    pass


class NotVotingCount(Count):
    pass


class PairedCount(Count):
    pass


class Vote(owl.Thing):
    group = Relation(OPENGOV, 'politicalGroup')
    role = StringProperty(OPENGOV, 'role')
    voter = Relation(SCHEMA, 'agent')
    vote_event = Relation(OPENGOV, 'voteEvent')
    option = StringProperty(OPENGOV, 'voteOption')

    class Meta:
        namespace = OPENGOV


class ContactDetail(owl.Thing):
    type = StringProperty(RDF, 'type')
    value = StringProperty(RDF, 'value')
    label = StringProperty(RDFS, 'label')
    valid_from = DateTimeProperty(SCHEMA, 'validFrom')
    note = StringProperty(SKOS, 'note')
    valid_until = DateTimeProperty(OPENGOV, 'validUntil')

    class Meta:
        namespace = OPENGOV
