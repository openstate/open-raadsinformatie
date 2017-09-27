import owl, schema, foaf, person, opengov
from .namespaces import OPENGOV, SCHEMA, COUNCIL
from owltology.property import Property, Instance, Type, Only, OnlyInteger, OnlyString, Exactly, MaxString


class Attachment(owl.Thing):
    #NAMESPACE = COUNCIL
    _type = Type(COUNCIL)
    contentUrl = Exactly(SCHEMA, 'contentUrl', 1, Property)
    fileSize = OnlyInteger(SCHEMA, 'fileSize')
    fileType = OnlyString(COUNCIL, 'fileType')
    additionalType = MaxString(SCHEMA, 'additionalType', 1)
    creator = Only(SCHEMA, 'creator', foaf.Agent)
    fileFormat = MaxString(SCHEMA, 'fileFormat', 1)


class Amendment(opengov.Motion):
    NAMESPACE = COUNCIL


class Bill(opengov.Motion):
    NAMESPACE = COUNCIL


class PrivateMembersBill(Bill):
    NAMESPACE = COUNCIL


class Petition(opengov.Motion):
    NAMESPACE = COUNCIL


class AgendaItem(schema.Event):
    _type = Type(COUNCIL)
    name = MaxString(SCHEMA, 'name', 1)
    description = MaxString(SCHEMA, 'description', 1)
    position = OnlyInteger(SCHEMA, 'position')
    attachment = Only(COUNCIL, 'attachment', Attachment)
    motion = Only(OPENGOV, 'motion', opengov.Motion)
    attendee = Only(SCHEMA, 'attendee', person.Person)  # not in owl
    absentee = Only(SCHEMA, 'absentee', person.Person)  # not in owl
    superEvent = Only(SCHEMA, 'superEvent', opengov.Event)
    #organizer = 'schema:organizer'
    #eventStatus = 'schema:eventStatus'


class VoteOption(owl.Thing):
    _type = Type(COUNCIL)
    # Instances
    VoteOptionYes = Instance(COUNCIL, 'VoteOptionYes')
    VoteOptionNo = Instance(COUNCIL, 'VoteOptionNo')
    VoteOptionAbstain = Instance(COUNCIL, 'VoteOptionAbstain')
    VoteOptionAbsent = Instance(COUNCIL, 'VoteOptionAbsent')
    VoteOptionNotVoting = Instance(COUNCIL, 'VoteOptionNotVoting')
    VoteOptionPaired = Instance(COUNCIL, 'VoteOptionPaired')
