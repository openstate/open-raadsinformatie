import owl, schema, foaf, ncal, person, org, govid
from .namespaces import OPENGOV, SCHEMA, COUNCIL, DCTERMS, NCAL, RDF
from owltology.property import Property, Type, Some, Only, Exactly, SomeString, SomeDate, Namespace


class Event(schema.Event):
    _type = Type(OPENGOV)
    attachment = Only(COUNCIL, 'attachment', 'council.Attachment')
    name = SomeString(SCHEMA, 'name')
    location = Some(SCHEMA, 'location', schema.Place)
    categories = Some(NCAL, 'categories', ncal.Category)
    agenda = Only(COUNCIL, 'agenda', list)
    motion = Only(OPENGOV, 'motion', 'opengov.Motion')
    attendee = Only(SCHEMA, 'attendee', person.Person)
    absentee = Only(SCHEMA, 'absentee', person.Person)
    organizer = Some(SCHEMA, 'organizer', foaf.Agent)
    eventStatus = Some(SCHEMA, 'eventStatus', schema.EventStatusType)

    ggmVrsNummer = govid.ggmVrsNummer
    ggmNummer = govid.ggmNummer
    ggmVolgnummer = govid.ggmVolgnummer


class Motion(owl.Thing):
    _type = Type(OPENGOV)
    name = SomeString(SCHEMA, 'name')
    legislativeSession = Some(OPENGOV, 'legislativeSession', Event)
    requirement = SomeString(OPENGOV, 'requirement')
    additionalType = SomeString(SCHEMA, 'additionalType')
    creator = Some(SCHEMA, 'creator', foaf.Agent)
    cocreator = Some(COUNCIL, 'cocreator', foaf.Agent)
    dateSubmitted = SomeDate(SCHEMA, 'dateSubmitted')
    #concluded
    publisher = Some(SCHEMA, 'publisher', foaf.Agent)
    text = SomeString(SCHEMA, 'text')
    voteEvent = Only(OPENGOV, 'voteEvent', 'opengov.VoteEvent')

    ggmVrsNummer = govid.ggmVrsNummer
    ggmNummer = govid.ggmNummer
    ggmVolgnummer = govid.ggmVolgnummer


class VoteEvent(schema.Event):
    _type = Type(OPENGOV)
    categories = Some(OPENGOV, 'categories', ncal.Category)
    created = SomeDate(DCTERMS, 'created')
    modified = SomeDate(DCTERMS, 'modified')
    motion = Exactly(OPENGOV, 'motion', 1, Motion)
    result = SomeString(OPENGOV, 'result')
    organizer = Some(SCHEMA, 'organizer', foaf.Agent)
    superEvent = Some(SCHEMA, 'superEvent', schema.Event)
    vote = Some(OPENGOV, 'vote', 'opengov.Vote')
    count = Some(OPENGOV, 'count', 'opengov.Count')


class Speech(owl.Thing):
    _type = Type(OPENGOV)


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
    _type = Type(OPENGOV)
    value = Exactly(RDF, 'value', 1, int)
    group = Exactly(OPENGOV, 'group', 1, org.Organization)


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
    _type = Type(OPENGOV)


class Result(owl.Thing):
    _type = Type(OPENGOV)
    # Instances
    ResultFail = 'opengov:ResultFail'
    ResultPass = 'opengov:ResultPass'
    ResultKept = 'council:ResultKept'
    ResultPostponed = 'council:ResultPostponed'
    ResultWithdrawn = 'council:ResultWithdrawn'
    ResultExpired = 'council:ResultExpired'
    ResultDiscussed = 'council:ResultDiscussed'
    ResultPublished = 'council:ResultPublished'


class ContactDetail(owl.Thing):
    _type = Type(OPENGOV)


class EventStatusType(schema.Event):
    _type = Type(OPENGOV)
    # Instances
    EventCancelled = 'schema:EventCancelled'
    EventPostponed = 'schema:EventPostponed'
    EventRescheduled = 'schema:EventRescheduled'
    EventScheduled = 'schema:EventScheduled'
    EventCompleted = 'council:EventCompleted'
