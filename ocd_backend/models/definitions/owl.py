"""The classes in this owl module are derived from and described by:
http://www.w3.org/2002/07/owl#
"""

from ocd_backend.models.definitions import Meta, Dcterms, Meeting, Ncal, Owl
from ocd_backend.models.model import Model
from ocd_backend.models.properties import Relation, StringProperty, ArrayProperty


class ABC(object):
    pass


class Thing(Owl, Model):
    classification = ArrayProperty(Ncal, 'categories')  # todo fix with popolo
    meta = Relation(Meta, 'meta')


class Identifier(Owl, Thing):
    identifier = StringProperty(Dcterms, 'identifier')
    represent = StringProperty(Meeting, 'represent')
