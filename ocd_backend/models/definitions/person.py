"""The classes in this person module are derived from and described by:
http://www.w3.org/ns/person#
"""

import foaf
from ocd_backend.models.definitions import Opengov, Schema, Foaf, Rdfs, \
    Dcterms, Bio, Person as PersonNS
from ocd_backend.models.properties import StringProperty, DateTimeProperty, \
    Relation


class Person(PersonNS, foaf.Agent):
    biography = StringProperty(Bio, 'biography')
    contact_details = Relation(Opengov, 'contactDetail')
    alternative_name = StringProperty(Dcterms, 'alternative')
    family_name = StringProperty(Foaf, 'familyName')
    gender = StringProperty(Foaf, 'gender')
    given_name = StringProperty(Foaf, 'givenName')
    name = StringProperty(Foaf, 'name')
    national_identity = StringProperty(Opengov, 'nationalIdentity')
    summary = StringProperty(Bio, 'olb')
    other_names = StringProperty(Opengov, 'otherName')
    links = StringProperty(Rdfs, 'seeAlso')
    birth_date = DateTimeProperty(Schema, 'birthDate')
    death_date = DateTimeProperty(Schema, 'deathDate')
    email = StringProperty(Schema, 'email')
    image = Relation(Schema, 'image')

    # def verbose_name(self):
    #     self.name = '%s %s' % (self.given_name, self.family_name)
