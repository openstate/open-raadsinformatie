from ..model import ModelBase
from ..property import InlineRelation, StringProperty, ArrayProperty
from .namespaces import OWL, META, DCTERMS, MEETING, EXT, NCAL


class Thing(ModelBase):
    ori_identifier = StringProperty(EXT, 'ori/identifier')
    identifier = InlineRelation(DCTERMS, 'identifier')  # todo different property?
    classification = ArrayProperty(NCAL, 'categories')  # todo fix with popolo
    meta = InlineRelation(META, 'meta')

    class Meta:
        namespace = OWL


class Identifier(Thing):
    identifier = StringProperty(DCTERMS, 'identifier')
    represent = StringProperty(MEETING, 'represent')

    class Meta:
        namespace = OWL
