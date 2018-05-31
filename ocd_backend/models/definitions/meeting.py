import opengov
import schema
from ..property import StringProperty, IntegerProperty, Relation, InlineRelation, Individual
from .namespaces import OPENGOV, SCHEMA, MEETING


class Meeting(schema.Event):
    """An assembly of people for a particular purpose, especially for formal
    discussion. Subclass of :class:`.schema.Event`
    """
    agenda = Relation(MEETING, 'agenda')
    attachment = InlineRelation(MEETING, 'attachment')
    motion = Relation(OPENGOV, 'motion')
    attendee = Relation(SCHEMA, 'attendee')
    audio = Relation(SCHEMA, 'audio')
    description = StringProperty(SCHEMA, 'description')
    status = Individual(SCHEMA, 'eventStatus') #todo InlineRelation ipv Individual?
    location = StringProperty(SCHEMA, 'location')
    name = StringProperty(SCHEMA, 'name', required=True)
    organization = Relation(SCHEMA, 'organizer')
    committee = Relation(MEETING, 'committee')
    parent = Relation(SCHEMA, 'superEvent')
    chair = StringProperty(MEETING, 'chair')
    absentee = Relation(SCHEMA, 'absentee')
    invitee = Relation(SCHEMA, 'invitee')

    class Meta:
        namespace = MEETING


class Amendment(opengov.Motion):
    """A proposal to modify another proposal. Subclass of
    :class:`.opengov.Motion`
    """
    amends = Relation(MEETING, 'amends')

    class Meta:
        namespace = MEETING


class AgendaItem(schema.Event):
    """An item in a list of topics to be discussed at an event. Subclass of
    :class:`.schema.Event`
    """
    attachment = InlineRelation(MEETING, 'attachment')
    motion = Relation(OPENGOV, 'motion')
    description = StringProperty(SCHEMA, 'description')
    name = StringProperty(SCHEMA, 'name')
    position = IntegerProperty(SCHEMA, 'position')
    parent = Relation(SCHEMA, 'superEvent')
    vote_event = Relation(OPENGOV, 'voteEvent')
    attendee = Relation(SCHEMA, 'attendee')
    absentee = Relation(SCHEMA, 'absentee')
    agenda = Relation(MEETING, 'agenda')

    class Meta:
        namespace = MEETING
        legacy_type = 'event'


# Result Individuals
ResultFail = Individual(OPENGOV, 'ResultFail')
ResultPass = Individual(OPENGOV, 'ResultPass')
ResultKept = Individual(MEETING, 'ResultKept')

ResultPostponed = Individual(MEETING, 'ResultPostponed')
ResultWithdrawn = Individual(MEETING, 'ResultWithdrawn')
ResultExpired = Individual(MEETING, 'ResultExpired')
ResultDiscussed = Individual(MEETING, 'ResultDiscussed')
ResultPublished = Individual(MEETING, 'ResultPublished')

# VoteOption Individuals
VoteOptionYes = Individual(OPENGOV, 'VoteOptionYes')
VoteOptionNo = Individual(OPENGOV, 'VoteOptionNo')
VoteOptionAbstain = Individual(OPENGOV, 'VoteOptionAbstain')
VoteOptionAbsent = Individual(OPENGOV, 'VoteOptionAbsent')
VoteOptionNotVoting = Individual(OPENGOV, 'VoteOptionNotVoting')
VoteOptionPaired = Individual(OPENGOV, 'VoteOptionPaired')
