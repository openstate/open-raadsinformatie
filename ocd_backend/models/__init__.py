"""Mapping names to the corresponding models.

This file is used to specify custom model mappings.
By mapping these names definitions can be remapped if needed later on.
"""
from .definitions import meeting, opengov, schema, person, org, prov


# https://argu.co/ns/meeting#
Meeting = meeting.Meeting
AgendaItem = meeting.AgendaItem
Report = meeting.Report
Amendment = meeting.Amendment
Committee = meeting.Committee

# http://www.w3.org/ns/opengov#
VoteEvent = opengov.VoteEvent
Motion = opengov.Motion
Result = opengov.Result
Count = opengov.Count
YesCount = opengov.YesCount
NoCount = opengov.NoCount
AbstainCount = opengov.AbstainCount
AbsentCount = opengov.AbsentCount
Vote = opengov.Vote

# http://schema.org/
MediaObject = schema.MediaObject
ImageObject = schema.ImageObject
CreativeWork = schema.CreativeWork
PropertyValue = schema.PropertyValue

# http://www.w3.org/ns/person#
Person = person.Person

# http://www.w3.org/ns/org#
Organization = org.Organization
# TopLevelOrganization is an alias for Organization
TopLevelOrganization = org.Organization
Membership = org.Membership

# http://www.w3.org/ns/prov#
Activity = prov.Activity

# Constants

ResultKept = meeting.ResultKept
ResultPostponed = meeting.ResultPostponed
ResultWithdrawn = meeting.ResultWithdrawn
ResultExpired = meeting.ResultExpired
ResultDiscussed = meeting.ResultDiscussed
ResultPublished = meeting.ResultPublished

ResultFailed = opengov.ResultFailed
ResultPassed = opengov.ResultPassed

EventCompleted = meeting.EventCompleted
EventConfirmed = meeting.EventConfirmed
EventUnconfirmed = meeting.EventUnconfirmed
EventScheduled = schema.EventScheduled
EventRescheduled = schema.EventRescheduled
EventCancelled = schema.EventCancelled
EventPostponed = schema.EventPostponed

VoteOptionYes = opengov.VoteOptionYes
VoteOptionNo = opengov.VoteOptionNo
VoteOptionAbstain = opengov.VoteOptionAbstain
VoteOptionAbsent = opengov.VoteOptionAbsent
VoteOptionNotVoting = opengov.VoteOptionNotVoting
VoteOptionPaired = opengov.VoteOptionPaired
