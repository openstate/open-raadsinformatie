"""Mapping names to the corresponding models.

This file is used to specify custom model mappings.
By mapping these names definitions can be remapped if needed later on.
"""
import definitions.foaf
import definitions.meeting
import definitions.ncal
import definitions.opengov
import definitions.org
import definitions.owl
import definitions.person
import definitions.schema

# https://argu.co/ns/meeting#
Meeting = definitions.meeting.Meeting
AgendaItem = definitions.meeting.AgendaItem
Amendment = definitions.meeting.Amendment

# https://argu.co/voc/mapping/
# OriIdentifier = definitions.mapping.OriIdentifier
# RunIdentifier = definitions.mapping.RunIdentifier
# MetadataIdentifier = definitions.mapping.MetadataIdentifier
# IbabsIdentifier = definitions.mapping.IbabsIdentifier
# NotubizIdentifier = definitions.mapping.NotubizIdentifier
# CbsIdentifier = definitions.mapping.CbsIdentifier
# AlmanakOrganizationName = definitions.mapping.AlmanakOrganizationName
# GGMIdentifier = definitions.mapping.GGMIdentifier

# http://www.w3.org/ns/opengov#
VoteEvent = definitions.opengov.VoteEvent
Motion = definitions.opengov.Motion
Result = definitions.opengov.Result
Count = definitions.opengov.Count
YesCount = definitions.opengov.YesCount
NoCount = definitions.opengov.NoCount
AbstainCount = definitions.opengov.AbstainCount
AbsentCount = definitions.opengov.AbsentCount
Vote = definitions.opengov.Vote

# http://schema.org/
MediaObject = definitions.schema.MediaObject
ImageObject = definitions.schema.ImageObject
CreativeWork = definitions.schema.CreativeWork
PropertyValue = definitions.schema.PropertyValue

# http://www.w3.org/ns/person#
Person = definitions.person.Person

# http://www.w3.org/ns/org#
Organization = definitions.org.Organization
# TopLevelOrganization is an alias for Organization
TopLevelOrganization = definitions.org.Organization
Membership = definitions.org.Membership

# Constants

ResultKept = definitions.meeting.ResultKept
ResultPostponed = definitions.meeting.ResultPostponed
ResultWithdrawn = definitions.meeting.ResultWithdrawn
ResultExpired = definitions.meeting.ResultExpired
ResultDiscussed = definitions.meeting.ResultDiscussed
ResultPublished = definitions.meeting.ResultPublished

ResultFailed = definitions.opengov.ResultFailed
ResultPassed = definitions.opengov.ResultPassed

EventCompleted = definitions.meeting.EventCompleted
EventConfirmed = definitions.meeting.EventConfirmed
EventUnconfirmed = definitions.meeting.EventUnconfirmed
EventScheduled = definitions.schema.EventScheduled
EventRescheduled = definitions.schema.EventRescheduled
EventCancelled = definitions.schema.EventCancelled
EventPostponed = definitions.schema.EventPostponed

VoteOptionYes = definitions.opengov.VoteOptionYes
VoteOptionNo = definitions.opengov.VoteOptionNo
VoteOptionAbstain = definitions.opengov.VoteOptionAbstain
VoteOptionAbsent = definitions.opengov.VoteOptionAbsent
VoteOptionNotVoting = definitions.opengov.VoteOptionNotVoting
VoteOptionPaired = definitions.opengov.VoteOptionPaired
