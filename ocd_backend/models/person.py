import foaf
from owltology.property import StringProperty, DateTimeProperty, Relation
from .namespaces import OPENGOV, SCHEMA, FOAF, RDFS, PERSON, DCTERMS, BIO


class Person(foaf.Agent):
    biography = StringProperty(BIO, 'biography')
    contact_details = Relation(OPENGOV, 'contactDetail')
    alternative_name = StringProperty(DCTERMS, 'alternative')
    family_name = StringProperty(FOAF, 'familyName')
    gender = StringProperty(FOAF, 'gender')
    given_name = StringProperty(FOAF, 'givenName')
    name = StringProperty(FOAF, 'name')
    national_identity = StringProperty(OPENGOV, 'nationalIdentity')
    summary = StringProperty(BIO, 'olb')
    other_names = StringProperty(OPENGOV, 'otherName')
    links = StringProperty(RDFS, 'seeAlso')
    birth_date = DateTimeProperty(SCHEMA, 'birthDate')
    death_date = DateTimeProperty(SCHEMA, 'deathDate')
    email = StringProperty(SCHEMA, 'email')
    image = Relation(SCHEMA, 'image')

    def verbose_name(self):
        self.name = '%s %s' % (self.given_name, self.family_name)

    class Meta:
        namespace = PERSON
