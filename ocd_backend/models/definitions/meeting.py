"""The classes in this ontology are defined by Argu BV. More details, current
definitions and information can be found here:
https://argu.co/ns/meeting#

The purpose of this ontology is to define meeting related classes that can be
used to describe both virtual (eg. online discussion) and non-virtual (eg.
an assembly of people) discussion.
"""

import opengov
import schema
from ocd_backend.models.definitions import Opengov, Schema, Meeting as MeetingNS
from ocd_backend.models.model import Individual
from ocd_backend.models.properties import StringProperty, IntegerProperty, \
    Relation, OrderedRelation


class Meeting(MeetingNS, schema.Event):
    """An assembly of people for a particular purpose, especially for formal
    discussion. Subclass of :class:`.schema.Event`
    """
    agenda = OrderedRelation(MeetingNS, 'agenda')
    attachment = Relation(MeetingNS, 'attachment')
    motion = Relation(Opengov, 'motion')
    attendee = Relation(Schema, 'attendee')
    audio = Relation(Schema, 'audio')
    description = StringProperty(Schema, 'description')
    status = Relation(Schema, 'eventStatus')
    location = StringProperty(Schema, 'location')
    name = StringProperty(Schema, 'name', required=True)
    organization = Relation(Schema, 'organizer', required=True)
    committee = Relation(MeetingNS, 'committee')
    parent = Relation(Schema, 'superEvent')
    chair = StringProperty(MeetingNS, 'chair')
    absentee = Relation(Schema, 'absentee')
    invitee = Relation(Schema, 'invitee')


class Amendment(MeetingNS, opengov.Motion):
    """A proposal to modify another proposal. Subclass of
    :class:`.opengov.Motion`
    """
    amends = Relation(MeetingNS, 'amends')


class AgendaItem(MeetingNS, schema.Event):
    """An item in a list of topics to be discussed at an event. Subclass of
    :class:`.schema.Event`
    """
    attachment = Relation(MeetingNS, 'attachment')
    motion = Relation(Opengov, 'motion')
    description = StringProperty(Schema, 'description')
    name = StringProperty(Schema, 'name', required=True)
    position = IntegerProperty(Schema, 'position')
    parent = Relation(Schema, 'superEvent', required=True)
    vote_event = Relation(Opengov, 'voteEvent')
    attendee = Relation(Schema, 'attendee')
    absentee = Relation(Schema, 'absentee')
    agenda = Relation(MeetingNS, 'agenda')


# Result Individuals
class ResultKept(MeetingNS, Individual):
    """When a proposal is kept for later processing"""
    pass


class ResultPostponed(MeetingNS, Individual):
    """When a proposal is postponed to a later (unspecified) moment"""
    pass


class ResultWithdrawn(MeetingNS, Individual):
    """When a proposal is withdrawn by its author"""
    pass


class ResultExpired(MeetingNS, Individual):
    """When a proposal has been expired"""
    pass


class ResultDiscussed(MeetingNS, Individual):
    """When a proposal has been discussed"""
    pass


class ResultPublished(MeetingNS, Individual):
    """When a proposal has been published"""
    pass


# EventStatusType Individuals
class EventCompleted(MeetingNS, Individual):
    """The event has taken place and has been completed"""
    pass


class EventConfirmed(MeetingNS, Individual):
    """The event will take place but has not been
    :class:`.schema.EventScheduled` yet
    """
    pass


class EventUnconfirmed(MeetingNS, Individual):
    """The event is not :class:`EventConfirmed` or is inactive"""
    pass
