"""The classes in this opengov module are derived from and described by:
http://www.w3.org/ns/opengov#
"""

import owl
import schema
from ..property import StringProperty, IntegerProperty, DateTimeProperty, ArrayProperty, Relation, InlineRelation
from ..model import Individual
from . import OPENGOV, SCHEMA, MEETING, DCTERMS, NCAL, RDF, RDFS, SKOS, BIBFRAME


class Motion(owl.Thing):
    attachment = InlineRelation(SCHEMA, 'attachment')
    legislative_session = StringProperty(OPENGOV, 'legislativeSession')
    requirement = StringProperty(OPENGOV, 'requirement')
    classification = StringProperty(SCHEMA, 'additionalType')
    creator = Relation(SCHEMA, 'creator')
    cocreator = Relation(MEETING, 'cocreator')
    date = DateTimeProperty(SCHEMA, 'dateSubmitted')
    name = StringProperty(SCHEMA, 'name')
    organization = Relation(SCHEMA, 'publisher')
    text = StringProperty(SCHEMA, 'text')
    vote_events = Relation(OPENGOV, 'voteEvent')


class VoteEvent(schema.Event):
    classification = ArrayProperty(NCAL, 'categories')
    created_at = DateTimeProperty(DCTERMS, 'created')
    updated_at = DateTimeProperty(DCTERMS, 'modified')
    motion = Relation(OPENGOV, 'motion')
    result = StringProperty(OPENGOV, 'result')
    organization = Relation(SCHEMA, 'organizer')
    legislative_session = Relation(SCHEMA, 'superEvent')
    votes = Relation(OPENGOV, 'vote')
    counts = Relation(OPENGOV, 'count')


class Speech(owl.Thing):
    attribution_text = StringProperty(OPENGOV, 'attributionText')
    audience = Relation(DCTERMS, 'audience')
    event = Relation(BIBFRAME, 'event')
    role = Relation(OPENGOV, 'role')
    audio = Relation(SCHEMA, 'audio')
    creator = Relation(SCHEMA, 'creator')
    end_date = DateTimeProperty(SCHEMA, 'endDate')
    position = IntegerProperty(SCHEMA, 'position')
    start_date = DateTimeProperty(SCHEMA, 'startDate')
    text = StringProperty(SCHEMA, 'text')
    video = StringProperty(SCHEMA, 'video')


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


class Count(owl.Thing):
    value = IntegerProperty(RDF, 'value')
    group = Relation(OPENGOV, 'group')


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


class Vote(owl.Thing):
    group = Relation(OPENGOV, 'politicalGroup')
    role = StringProperty(OPENGOV, 'role')
    voter = Relation(SCHEMA, 'agent')
    vote_event = Relation(OPENGOV, 'voteEvent')
    option = StringProperty(OPENGOV, 'voteOption')


class ContactDetail(owl.Thing):
    type = StringProperty(RDF, 'type')
    value = StringProperty(RDF, 'value')
    label = StringProperty(RDFS, 'label')
    valid_from = DateTimeProperty(SCHEMA, 'validFrom')
    note = StringProperty(SKOS, 'note')
    valid_until = DateTimeProperty(OPENGOV, 'validUntil')


class Result(owl.Thing):
    text = StringProperty(SCHEMA, 'text')
    vote_event = Relation(OPENGOV, 'voteEvent')


# Result Individuals
class ResultFail(Individual):
    """When a decision is made in favor of a proposal"""
    pass


class ResultPass(Individual):
    """When a decision is made against a proposal"""
    pass


# VoteOption Individuals
class VoteOptionYes(Individual):
    """When an individual votes in favor of a proposal"""
    pass


class VoteOptionNo(Individual):
    """When an individual votes against a proposal"""
    pass


class VoteOptionAbstain(Individual):
    """When an individual abstained from voting"""
    pass


class VoteOptionAbsent(Individual):
    """When an individual did not vote due to being absent"""
    pass


class VoteOptionNotVoting(Individual):
    """When an individual is not voting"""
    pass


class VoteOptionPaired(Individual):
    """When an individual entered a reciprocal agreement with another voter by
    which the voter abstains if the other is unable to vote. It may not be
    known which two members form a pair.
    """
    pass
