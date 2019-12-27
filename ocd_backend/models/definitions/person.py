"""The classes in this person module are derived from and described by:
http://www.w3.org/ns/person#
"""

import foaf
from ocd_backend.models.definitions import Opengov, Schema, Foaf, Rdfs, \
    Dcterms, Bio, Vcard, Person as PersonNS, Meeting
from ocd_backend.models.properties import StringProperty, URLProperty, DateTimeProperty, \
    Relation


class Person(PersonNS, foaf.Agent):
    biography = StringProperty(Bio, 'biography')
    contact_details = Relation(Opengov, 'contactDetail')
    alternative_name = StringProperty(Dcterms, 'alternative')
    family_name = StringProperty(Foaf, 'familyName')
    gender = StringProperty(Foaf, 'gender')
    given_name = StringProperty(Foaf, 'givenName')
    additional_name = StringProperty(Schema, 'additionalName')
    home_location = StringProperty(Schema, 'homeLocation')
    honorific_prefix = StringProperty(Schema, 'honorificPrefix')
    honorific_suffix = StringProperty(Schema, 'honorificSuffix')
    nickname = StringProperty(Vcard, 'nickname')
    initials = StringProperty(Meeting, 'initials')
    name = StringProperty(Foaf, 'name')
    national_identity = StringProperty(Opengov, 'nationalIdentity')
    summary = StringProperty(Bio, 'olb')
    other_names = StringProperty(Opengov, 'otherName')
    links = URLProperty(Rdfs, 'seeAlso')
    birth_place = StringProperty(Schema, 'birthPlace')
    birth_date = DateTimeProperty(Schema, 'birthDate')
    death_date = DateTimeProperty(Schema, 'deathDate')
    email = StringProperty(Schema, 'email')
    image = Relation(Schema, 'image')
    phone = StringProperty(Schema, 'telephone')
