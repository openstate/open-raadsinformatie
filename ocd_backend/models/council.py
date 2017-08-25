from ocd_backend.models import owl, opengov, schema


class Attachment(owl.Thing):
    pass


class Amendment(opengov.Motion):
    pass


class Bill(opengov.Motion):
    pass


class PrivateMembersBill(Bill):
    pass


class Petition(opengov.Motion):
    pass


class AgendaItem(schema.Event):
    name = 'schema:name'
    description = 'schema:description'
    position = 'schema:position'
    attachment = 'council:hasAgendaItem'
    motion = 'opengov:motion'
    attendee = 'schema:attendee'
    absentee = 'schema:absentee'
    organizer = 'schema:organizer'
    eventStatus = 'schema:eventStatus'


class VoteOption(owl.Thing):
    # Instances
    VoteOptionYes = 'council:VoteOptionYes'
    VoteOptionNo = 'council:VoteOptionNo'
    VoteOptionAbstain = 'council:VoteOptionAbstain'
    VoteOptionAbsent = 'council:VoteOptionAbsent'
    VoteOptionNotVoting = 'council:VoteOptionNotVoting'
    VoteOptionPaired = 'council:VoteOptionPaired'
