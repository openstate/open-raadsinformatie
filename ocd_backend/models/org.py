from ocd_backend.models import owl, foaf


class Membership(owl.Thing):
    pass


class Role(owl.Thing):
    pass


class Organization(foaf.Agent):
    name = 'skos:prefLabel'
