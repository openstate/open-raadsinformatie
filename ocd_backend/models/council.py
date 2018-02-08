import owl, schema, opengov, govid
from .namespaces import OPENGOV, SCHEMA, COUNCIL
from owltology.property import StringProperty, IntegerProperty, Relation


class Attachment(owl.Thing):
    name = StringProperty(SCHEMA, 'name')
    url = StringProperty(SCHEMA, 'contentUrl')
    size_in_bytes = IntegerProperty(SCHEMA, 'fileSize')
    file_type = StringProperty(COUNCIL, 'fileType')
    additional_type = StringProperty(SCHEMA, 'additionalType')
    creator = Relation(SCHEMA, 'creator')
    content_type = StringProperty(SCHEMA, 'fileFormat')
    original_url = StringProperty(SCHEMA, 'isBasedOn')
    text = StringProperty(SCHEMA, 'text')

    class Meta:
        namespace = COUNCIL
        enricher_task = 'file_to_text'


class Amendment(opengov.Motion):
    amends = Relation(COUNCIL, 'amends')

    class Meta:
        namespace = COUNCIL


class Bill(opengov.Motion):
    class Meta:
        namespace = COUNCIL


class PrivateMembersBill(Bill):
    class Meta:
        namespace = COUNCIL


class Petition(opengov.Motion):
    class Meta:
        namespace = COUNCIL


class AgendaItem(schema.Event):
    attachment = Relation(COUNCIL, 'attachment')
    motion = Relation(OPENGOV, 'motion')
    description = StringProperty(SCHEMA, 'description')
    name = StringProperty(SCHEMA, 'name')
    position = IntegerProperty(SCHEMA, 'position')
    parent = Relation(SCHEMA, 'superEvent')
    vote_event = Relation(OPENGOV, 'voteEvent')
    attendee = Relation(SCHEMA, 'attendee')
    absentee = Relation(SCHEMA, 'absentee')
    agenda = Relation(COUNCIL, 'agenda')

    ggm_nummer = govid.ggm_nummer

    class Meta:
        namespace = COUNCIL
        legacy_type = 'event_item'


class Result(owl.Thing):
    text = StringProperty(SCHEMA, 'text')
    vote_event = Relation(OPENGOV, 'voteEvent')

    # Instances
    ResultFail = 'opengov:ResultFail'
    ResultPass = 'opengov:ResultPass'
    ResultKept = 'council:ResultKept'
    ResultPostponed = 'council:ResultPostponed'
    ResultWithdrawn = 'council:ResultWithdrawn'
    ResultExpired = 'council:ResultExpired'
    ResultDiscussed = 'council:ResultDiscussed'
    ResultPublished = 'council:ResultPublished'

    class Meta:
        namespace = COUNCIL


class VoteOption(owl.Thing):
    # Instances
    VoteOptionYes = 'council:VoteOptionYes'
    VoteOptionNo = 'council:VoteOptionNo'
    VoteOptionAbstain = 'council:VoteOptionAbstain'
    VoteOptionAbsent = 'council:VoteOptionAbsent'
    VoteOptionNotVoting = 'council:VoteOptionNotVoting'
    VoteOptionPaired = 'council:VoteOptionPaired'

    class Meta:
        namespace = COUNCIL
