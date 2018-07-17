"""The classes in this foaf module are derived from and described by:
http://xmlns.com/foaf/0.1/
"""

import owl
from ocd_backend.models.definitions import ORG
from ocd_backend.models.properties import Relation


class Agent(owl.Thing):
    has_member = Relation(ORG, 'hasMember')
    member_of = Relation(ORG, 'memberOf')
