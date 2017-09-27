import foaf
import ncal
import opengov
import org
import council
import owl
import person
import schema
import govid

# This file is used to specify custom mappings

# Mapping names to the corresponding models
# By mapping these names definitions can be remapped if needed later on.
Event = opengov.Event
VoteEvent = opengov.VoteEvent
Organization = org.Organization
EventStatusType = opengov.EventStatusType
Motion = opengov.Motion
Amendment = council.Amendment
Bill = council.Bill
PrivateMembersBill = council.PrivateMembersBill
Petition = council.Petition
Result = opengov.Result
Count = opengov.Count
YesCount = opengov.YesCount
NoCount = opengov.NoCount
AbstainCount = opengov.AbstainCount
AbsentCount = opengov.AbsentCount
Vote = opengov.Vote
VoteOption = council.VoteOption
Person = person.Person
Attachment = council.Attachment
ImageObject = schema.ImageObject
PropertyValue = schema.PropertyValue
AgendaItem = council.AgendaItem
ggmIdentifier = govid.ggmIdentifier
ggmVrsNummer = govid.ggmVrsNummer
ggmNummer = govid.ggmNummer
oriIdentifier = govid.oriIdentifier

# TEMP
# Mandatory URI for JsonLD
CONTEXT = '@context'
ID = '@id'
TYPE = '@type'
HIDDEN = 'hidden'

context = {
    "foaf": "http://xmlns.com/foaf/0.1/",
    "ncal": "http://www.semanticdesktop.org/ontologies/2007/04/02/ncal#",
    "opengov": "http://www.w3.org/ns/opengov#",
    "org": "http://www.w3.org/ns/org#",
    "council": "https://argu.co/ns/0.1/gov/council#",
    "govid": "https://argu.co/ns/0.1/gov/id#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "person": "http://www.w3.org/ns/person#",
    "schema": "http://schema.org/",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",

    "council:agenda": {
        "@type": "@id",
        "@container": "@list"
    },
    "schema:attendee": {
        "@type": "@id"
    },
    "opengov:vote": {
        "@type": "@id"
    },
    "opengov:count": {
        "@type": "@id"
    },
    "opengov:voteEvent": {
        "@type": "@id"
    },
    "opengov:motion": {
        "@type": "@id"
    }
}
