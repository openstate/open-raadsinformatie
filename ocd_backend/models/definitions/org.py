"""The classes in this org module are derived from and described by:
http://www.w3.org/ns/org#
"""

from ocd_backend.models.definitions import foaf, owl
from ocd_backend.models.definitions import Org, Skos, Opengov, Dcterms, \
    Schema, Rdf, Meta, Vcard
from ocd_backend.models.properties import StringProperty, URLProperty, DateTimeProperty, \
    Relation, OrderedRelation


class Membership(Org, owl.Thing):
    label = StringProperty(Skos, 'prefLabel')
    member = Relation(Org, 'member')
    organization = Relation(Org, 'organization')
    role = StringProperty(Org, 'role')
    start_date = DateTimeProperty(Schema, 'validFrom')
    end_date = DateTimeProperty(Opengov, 'validUntil')


class Role(Org, owl.Thing):
    pass


class Organization(Org, foaf.Agent):
    area = Relation(Opengov, 'area')
    contact_details = Relation(Opengov, 'contactDetail')
    abstract = StringProperty(Dcterms, 'abstract')
    description = StringProperty(Dcterms, 'description')
    classification = StringProperty(Org, 'classification')
    subOrganizationOf = OrderedRelation(Org, 'subOrganizationOf')
    other_names = StringProperty(Opengov, 'otherName')
    links = URLProperty(Rdf, 'seeAlso')
    dissolution_date = StringProperty(Schema, 'dissolutionDate')
    founding_date = StringProperty(Schema, 'foundingDate')
    image = StringProperty(Schema, 'image')
    alt_label = StringProperty(Skos, 'altLabel')
    name = StringProperty(Skos, 'prefLabel')
    collection = StringProperty(Meta, 'collection')
    homepage = URLProperty(Vcard, 'url')
    email = StringProperty(Vcard, 'email')
