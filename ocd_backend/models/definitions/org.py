"""The classes in this org module are derived from and described by:
http://www.w3.org/ns/org#
"""

import foaf
import owl
from ocd_backend.models.definitions import Org, Skos, Opengov, Dcterms, \
    Schema, Rdf, Meta
from ocd_backend.models.properties import StringProperty, DateTimeProperty, \
    Relation, OrderedRelation


class Membership(Org, owl.Thing):
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
    parent = OrderedRelation(Org, 'subOrganizationOf')
    other_names = StringProperty(Opengov, 'otherName')
    links = StringProperty(Rdf, 'seeAlso')
    dissolution_date = StringProperty(Schema, 'dissolutionDate')
    founding_date = StringProperty(Schema, 'foundingDate')
    image = StringProperty(Schema, 'image')
    alt_label = StringProperty(Skos, 'altLabel')
    name = StringProperty(Skos, 'prefLabel')
    collection = StringProperty(Meta, 'collection')
