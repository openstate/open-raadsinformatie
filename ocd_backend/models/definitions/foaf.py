"""The classes in this foaf module are derived from and described by:
http://xmlns.com/foaf/0.1/
"""

import owl
from ocd_backend.models.definitions import Org, Foaf
from ocd_backend.models.properties import Relation


class Agent(Foaf, owl.Thing):
    has_member = Relation(Org, 'hasMember')
    member_of = Relation(Org, 'memberOf')
