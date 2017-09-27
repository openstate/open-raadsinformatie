import owl, foaf
from .namespaces import ORG


class Membership(owl.Thing):
    NAMESPACE = ORG


class Role(owl.Thing):
    NAMESPACE = ORG


class Organization(foaf.Agent):
    NAMESPACE = ORG
    name = 'skos:prefLabel'
