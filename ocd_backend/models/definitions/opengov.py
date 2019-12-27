"""The classes in this opengov module are derived from and described by:
http://www.w3.org/ns/opengov#
"""

import owl
import schema
from ocd_backend.models.definitions import Opengov, Schema, Meeting, Dcterms, \
    Ncal, Rdf, Rdfs, Skos, Bibframe
from ocd_backend.models.properties import StringProperty, IntegerProperty, \
    DateProperty, DateTimeProperty, ArrayProperty, Relation
from ocd_backend.models.misc import Uri


class Motion(Opengov, owl.Thing):
    attachment = Relation(Schema, 'attachment')
    legislative_session = StringProperty(Opengov, 'legislativeSession')
    requirement = StringProperty(Opengov, 'requirement')
    classification = StringProperty(Schema, 'additionalType')
    status = StringProperty(Meeting, 'status')
    creator = Relation(Schema, 'creator')
    cocreator = Relation(Meeting, 'cocreator')
    date = DateProperty(Schema, 'dateSubmitted')
    name = StringProperty(Schema, 'name')
    organization = Relation(Schema, 'publisher')
    is_referenced_by = Relation(Dcterms, 'isReferencedBy')
    text = StringProperty(Schema, 'text')
    result = StringProperty(Opengov, 'result')
    vote_event = Relation(Opengov, 'voteEvent')


class VoteEvent(Opengov, schema.Event):
    classification = ArrayProperty(Ncal, 'categories')
    created_at = DateTimeProperty(Dcterms, 'created')
    updated_at = DateTimeProperty(Dcterms, 'modified')
    motion = Relation(Opengov, 'motion')
    result = StringProperty(Opengov, 'result')
    organization = Relation(Schema, 'organizer')
    legislative_session = StringProperty(Opengov, 'legislativeSession')
    votes = Relation(Opengov, 'vote')
    counts = Relation(Opengov, 'count')


class Speech(Opengov, owl.Thing):
    attribution_text = StringProperty(Opengov, 'attributionText')
    audience = Relation(Dcterms, 'audience')
    event = Relation(Bibframe, 'event')
    role = Relation(Opengov, 'role')
    audio = Relation(Schema, 'audio')
    creator = Relation(Schema, 'creator')
    end_date = DateTimeProperty(Schema, 'endDate')
    position = IntegerProperty(Schema, 'position')
    start_date = DateTimeProperty(Schema, 'startDate')
    text = StringProperty(Schema, 'text')
    video = StringProperty(Schema, 'video')


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


class Count(Opengov, owl.Thing):
    value = IntegerProperty(Rdf, 'value')
    group = Relation(Opengov, 'group')


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


class Vote(Opengov, owl.Thing):
    group = Relation(Opengov, 'politicalGroup')
    role = StringProperty(Opengov, 'role')
    voter = Relation(Schema, 'agent')
    vote_event = Relation(Opengov, 'voteEvent')
    option = StringProperty(Opengov, 'voteOption')
    weight = IntegerProperty(Opengov, 'weight')


class ContactDetail(Opengov, owl.Thing):
    type = StringProperty(Rdf, 'type')
    value = StringProperty(Rdf, 'value')
    label = StringProperty(Rdfs, 'label')
    valid_from = DateTimeProperty(Schema, 'validFrom')
    note = StringProperty(Skos, 'note')
    valid_until = DateTimeProperty(Opengov, 'validUntil')


class Result(Opengov, owl.Thing):
    text = StringProperty(Schema, 'text')
    vote_event = Relation(Opengov, 'voteEvent')


ResultFailed = Uri(Opengov, "ResultFailed")
ResultPassed = Uri(Opengov, "ResultPassed")


VoteOptionYes = Uri(Opengov, "VoteOptionYes")
VoteOptionNo = Uri(Opengov, "VoteOptionNo")
VoteOptionAbstain = Uri(Opengov, "VoteOptionAbstain")
VoteOptionAbsent = Uri(Opengov, "VoteOptionAbsent")
VoteOptionNotVoting = Uri(Opengov, "VoteOptionNotVoting")
VoteOptionPaired = Uri(Opengov, "VoteOptionPaired")
