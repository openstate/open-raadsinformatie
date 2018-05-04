import foaf
import ncal
import opengov
import org
import council
import owl
import person
import schema
import govid
import meta

# This file is used to specify custom mappings

# Mapping names to the corresponding models
# By mapping these names definitions can be remapped if needed later on.
Event = opengov.Event
VoteEvent = opengov.VoteEvent
Organization = org.Organization
Motion = opengov.Motion
Amendment = council.Amendment
Bill = council.Bill
PrivateMembersBill = council.PrivateMembersBill
Petition = council.Petition
Result = council.Result
Count = opengov.Count
YesCount = opengov.YesCount
NoCount = opengov.NoCount
AbstainCount = opengov.AbstainCount
AbsentCount = opengov.AbsentCount
Vote = opengov.Vote
Person = person.Person
Attachment = council.Attachment
ImageObject = schema.ImageObject
PropertyValue = schema.PropertyValue
AgendaItem = council.AgendaItem
Metadata = meta.Metadata

ggm_identifier = govid.ggm_identifier
ggm_vrsnummer = govid.ggm_vrsnummer
ggm_nummer = govid.ggm_nummer
ori_identifier = govid.ori_identifier
