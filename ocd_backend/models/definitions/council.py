import govid
import opengov
import owl
import schema
from ..property import StringProperty, IntegerProperty, Relation, InlineRelation, Instance
from .namespaces import OPENGOV, SCHEMA, COUNCIL


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
    attachment = InlineRelation(COUNCIL, 'attachment')
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
    # Naar opengov namespace
    text = StringProperty(SCHEMA, 'text')
    vote_event = Relation(OPENGOV, 'voteEvent')

    class Meta:
        namespace = COUNCIL


# Instances Result
ResultFail = Instance(OPENGOV, 'ResultFail')
ResultPass = Instance(OPENGOV, 'ResultPass')
ResultKept = Instance(COUNCIL, 'ResultKept')
# todo wat betekent het
ResultPostponed = Instance(COUNCIL, 'ResultPostponed')
ResultWithdrawn = Instance(COUNCIL, 'ResultWithdrawn')
ResultExpired = Instance(COUNCIL, 'ResultExpired')
ResultDiscussed = Instance(COUNCIL, 'ResultDiscussed')
ResultPublished = Instance(COUNCIL, 'ResultPublished')

# Instances VoteOption
VoteOptionYes = Instance(OPENGOV, 'VoteOptionYes')
VoteOptionNo = Instance(OPENGOV, 'VoteOptionNo')
VoteOptionAbstain = Instance(OPENGOV, 'VoteOptionAbstain')
VoteOptionAbsent = Instance(OPENGOV, 'VoteOptionAbsent')
VoteOptionNotVoting = Instance(OPENGOV, 'VoteOptionNotVoting')
VoteOptionPaired = Instance(OPENGOV, 'VoteOptionPaired')
