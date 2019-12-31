"""The classes in this ontology are defined by Argu BV. More details, current
definitions and information can be found here:
https://argu.co/ns/meeting#

The purpose of this ontology is to define meeting related classes that can be
used to describe both virtual (eg. online discussion) and non-virtual (eg.
an assembly of people) discussion.
"""

import opengov
import schema
import org
from ocd_backend.models.definitions import Opengov, Schema, Meeting as MeetingNS
from ocd_backend.models.properties import StringProperty, URLProperty, IntegerProperty, \
    Relation, OrderedRelation, DateTimeProperty
from ocd_backend.models.misc import Uri
from ocd_backend.loaders.delta import DeltaLoader


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
    status = URLProperty(Schema, 'eventStatus')
    location = StringProperty(Schema, 'location')
    name = StringProperty(Schema, 'name', required=True)
    organization = Relation(Schema, 'organizer')
    committee = Relation(MeetingNS, 'committee')
    parent = Relation(Schema, 'superEvent')
    chair = StringProperty(MeetingNS, 'chair')
    absentee = Relation(Schema, 'absentee')
    invitee = Relation(Schema, 'invitee')
    replaces = Relation(MeetingNS, 'replaces')
    replaced_by = Relation(MeetingNS, 'replaced_by')


class Report(MeetingNS, schema.Event, schema.CreativeWork):
    description = StringProperty(Schema, 'description')
    result = StringProperty(Opengov, 'result')
    attachment = Relation(MeetingNS, 'attachment')


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
    last_discussed_at = DateTimeProperty(MeetingNS, 'lastDiscussedAt', ignore_for_loader=[DeltaLoader,])


class Committee(MeetingNS, org.Organization):
    pass


ResultKept = Uri(MeetingNS, "ResultKept")
ResultPostponed = Uri(MeetingNS, "ResultPostponed")
ResultWithdrawn = Uri(MeetingNS, "ResultWithdrawn")
ResultExpired = Uri(MeetingNS, "ResultExpired")
ResultDiscussed = Uri(MeetingNS, "ResultDiscussed")
ResultPublished = Uri(MeetingNS, "ResultPublished")


EventCompleted = Uri(MeetingNS, "EventCompleted")
EventConfirmed = Uri(MeetingNS, "EventConfirmed")
EventUnconfirmed = Uri(MeetingNS, "EventUnconfirmed")
