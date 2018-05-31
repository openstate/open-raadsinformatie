import owl
from ..property import Relation
from .namespaces import FOAF, ORG


class Agent(owl.Thing):
    has_member = Relation(ORG, 'hasMember')
    member_of = Relation(ORG, 'memberOf')

    class Meta:
        namespace = FOAF
