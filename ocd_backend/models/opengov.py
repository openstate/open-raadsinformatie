from ocd_backend.models import owl, schema

NAMESPACE = "opengov"


class Motion(owl.Thing):
    name = 'schema:name'
    legislativeSession = 'opengov:legislativeSession'
    requirement = 'opengov:requirement'
    additionalType = 'schema:additionalType'
    creator = "schema:creator"
    dateSubmitted = "schema:dateSubmitted"
    publisher = "schema:publisher"
    text = "schema:text"
    voteEvent = "opengov:voteEvent"


class Speech(owl.Thing):
    pass


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
    value = 'rdf:value'
    group = 'opengov:group'


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
    pass


class Result(owl.Thing):
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
    pass


class Event(schema.Event):
    name = 'schema:name'
    location = 'schema:location'
    categories = 'ncal:categories'
    hasAgendaItem = 'council:hasAgendaItem'
    motion = 'opengov:motion'
    attendee = 'schema:attendee'
    absentee = 'schema:absentee'
    organizer = 'schema:organizer'
    eventStatus = 'schema:eventStatus'


class EventStatusType(schema.Event):
    # Instances
    EventCancelled = 'schema:EventCancelled'
    EventPostponed = 'schema:EventPostponed'
    EventRescheduled = 'schema:EventRescheduled'
    EventScheduled = 'schema:EventScheduled'
    EventCompleted = 'council:EventCompleted'


class VoteEvent(schema.Event):
    categories = 'opengov:categories'
    created = 'dcterms:created'
    modified = 'dcterms:modified'
    motion = 'opengov:motion'
    result = 'opengov:result'
    organizer = 'schema:organizer'
    superEvent = 'schema:superEvent'
    vote = 'opengov:vote'
    count = 'opengov:count'
