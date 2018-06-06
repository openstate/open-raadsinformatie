"""The classes in this owl module are derived from and described by:
http://www.w3.org/2002/07/owl#
"""

from ..model import ModelBase
from ..property import InlineRelation, StringProperty, ArrayProperty
from . import META, DCTERMS, MEETING, NCAL


class Thing(ModelBase):
    derived_from = InlineRelation(DCTERMS, 'derivedFrom')  # todo prov onto
    classification = ArrayProperty(NCAL, 'categories')  # todo fix with popolo
    meta = InlineRelation(META, 'meta')


class Identifier(Thing):
    identifier = StringProperty(DCTERMS, 'identifier')
    represent = StringProperty(MEETING, 'represent')
