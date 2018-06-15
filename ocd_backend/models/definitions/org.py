"""The classes in this org module are derived from and described by:
http://www.w3.org/ns/org#
"""

import foaf
import owl
from ..properties import StringProperty, DateTimeProperty, Relation, OrderedRelation
from . import ORG, SKOS, OPENGOV, DCTERMS, SCHEMA, RDF


class Membership(owl.Thing):
    member = Relation(ORG, 'member')
    organization = Relation(ORG, 'organization')
    role = StringProperty(ORG, 'role')
    start_date = DateTimeProperty(SCHEMA, 'validFrom')
    end_date = DateTimeProperty(OPENGOV, 'validUntil')


class Role(owl.Thing):
    pass


class Organization(foaf.Agent):
    area = Relation(OPENGOV, 'area')
    contact_details = Relation(OPENGOV, 'contactDetail')
    abstract = StringProperty(DCTERMS, 'abstract')
    description = StringProperty(DCTERMS, 'description')
    classification = StringProperty(ORG, 'classification')
    parent = OrderedRelation(ORG, 'subOrganizationOf')
    other_names = StringProperty(OPENGOV, 'otherName')
    links = StringProperty(RDF, 'seeAlso')
    dissolution_date = StringProperty(SCHEMA, 'dissolutionDate')
    founding_date = StringProperty(SCHEMA, 'foundingDate')
    image = StringProperty(SCHEMA, 'image')
    alt_label = StringProperty(SKOS, 'altLabel')
    name = StringProperty(SKOS, 'prefLabel')
