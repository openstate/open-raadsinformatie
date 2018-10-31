"""The classes in this opengov module are derived from and described by:
http://www.w3.org/ns/opengov#
"""

import owl
import schema
from ocd_backend.models.definitions import Opengov, Schema, Meeting, Dcterms, \
    Ncal, Rdf, Rdfs, Skos, Bibframe
from ocd_backend.models.model import Individual
from ocd_backend.models.properties import StringProperty, IntegerProperty, \
    DateProperty, DateTimeProperty, ArrayProperty, Relation


class Motion(Opengov, owl.Thing):
    attachment = Relation(Schema, 'attachment')
    legislative_session = StringProperty(Opengov, 'legislativeSession')
    requirement = StringProperty(Opengov, 'requirement')
    classification = StringProperty(Schema, 'additionalType')
    creator = Relation(Schema, 'creator')
    cocreator = Relation(Meeting, 'cocreator')
    date = DateProperty(Schema, 'dateSubmitted')
    name = StringProperty(Schema, 'name')
    organization = Relation(Schema, 'publisher')
    text = StringProperty(Schema, 'text')
    vote_events = Relation(Opengov, 'voteEvent')


class VoteEvent(Opengov, schema.Event):
    classification = ArrayProperty(Ncal, 'categories')
    created_at = DateTimeProperty(Dcterms, 'created')
    updated_at = DateTimeProperty(Dcterms, 'modified')
    motion = Relation(Opengov, 'motion')
    result = Relation(Opengov, 'result')
    organization = Relation(Schema, 'organizer')
    legislative_session = Relation(Schema, 'superEvent')
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
    option = Relation(Opengov, 'voteOption')
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


# Result Individuals
class ResultFail(Opengov, Individual):
    """When a decision is made against a proposal"""
    pass


class ResultPass(Opengov, Individual):
    """When a decision is made in favor of a proposal"""
    pass


# VoteOption Individuals
class VoteOptionYes(Opengov, Individual):
    """When an individual votes in favor of a proposal"""
    pass


class VoteOptionNo(Opengov, Individual):
    """When an individual votes against a proposal"""
    pass


class VoteOptionAbstain(Opengov, Individual):
    """When an individual abstained from voting"""
    pass


class VoteOptionAbsent(Opengov, Individual):
    """When an individual did not vote due to being absent"""
    pass


class VoteOptionNotVoting(Opengov, Individual):
    """When an individual is not voting"""
    pass


class VoteOptionPaired(Opengov, Individual):
    """When an individual entered a reciprocal agreement with another voter by
    which the voter abstains if the other is unable to vote. It may not be
    known which two members form a pair.
    """
    pass
