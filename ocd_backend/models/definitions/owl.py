"""The classes in this owl module are derived from and described by:
http://www.w3.org/2002/07/owl#
"""

from ocd_backend.models.definitions import META, DCTERMS, MEETING, NCAL
from ocd_backend.models.model import Model
from ocd_backend.models.properties import Relation, StringProperty, ArrayProperty


class Thing(Model):
    classification = ArrayProperty(NCAL, 'categories')  # todo fix with popolo
    meta = Relation(META, 'meta')


class Identifier(Thing):
    identifier = StringProperty(DCTERMS, 'identifier')
    represent = StringProperty(MEETING, 'represent')
