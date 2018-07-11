"""The classes in this ontology are defined by Argu BV. More details, current
definitions and information can be found here:
https://argu.co/ns/meeting#

The purpose of this ontology is to define meeting related classes that can be
used to describe both virtual (eg. online discussion) and non-virtual (eg.
an assembly of people) discussion.
"""

import opengov
import schema
from ..properties import StringProperty, IntegerProperty, Relation, InlineRelation
from ..model import Individual
from . import OPENGOV, SCHEMA, MEETING


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
    status = Relation(SCHEMA, 'eventStatus')
    location = StringProperty(SCHEMA, 'location')
    name = StringProperty(SCHEMA, 'name', required=True)
    organization = Relation(SCHEMA, 'organizer')
    committee = Relation(MEETING, 'committee')
    parent = Relation(SCHEMA, 'superEvent')
    chair = StringProperty(MEETING, 'chair')
    absentee = Relation(SCHEMA, 'absentee')
    invitee = Relation(SCHEMA, 'invitee')


class Amendment(opengov.Motion):
    """A proposal to modify another proposal. Subclass of
    :class:`.opengov.Motion`
    """
    amends = Relation(MEETING, 'amends')


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


# Result Individuals
class ResultKept(Individual):
    """When a proposal is kept for later processing"""
    pass


class ResultPostponed(Individual):
    """When a proposal is postponed to a later (unspecified) moment"""
    pass


class ResultWithdrawn(Individual):
    """When a proposal is withdrawn by its author"""
    pass


class ResultExpired(Individual):
    """When a proposal has been expired"""
    pass


class ResultDiscussed(Individual):
    """When a proposal has been discussed"""
    pass


class ResultPublished(Individual):
    """When a proposal has been published"""
    pass


# EventStatusType Individuals
class EventCompleted(Individual):
    """The event has taken place and has been completed"""
    pass


class EventConfirmed(Individual):
    """The event will take place but has not been
    :class:`.schema.EventScheduled` yet
    """
    pass


class EventUnconfirmed(Individual):
    """The event is not :class:`EventConfirmed` or is inactive"""
    pass
