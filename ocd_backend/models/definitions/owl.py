"""The classes in this owl module are derived from and described by:
http://www.w3.org/2002/07/owl#
"""

from ocd_backend.models.definitions import Meta, Dcterms, Meeting, Ncal, Owl, Vcard
from ocd_backend.models.model import Model
from ocd_backend.models.properties import Relation, StringProperty, ArrayProperty


class Thing(Owl, Model):
    classification = ArrayProperty(Ncal, 'categories')  # todo fix with popolo
    meta = Relation(Meta, 'meta')
    has_organization_name = Relation(Vcard, 'hasOrganizationName', required=True)


class TopLevelThing(Owl, Model):
    classification = ArrayProperty(Ncal, 'categories')  # todo fix with popolo
    meta = Relation(Meta, 'meta')


class Identifier(Thing):
    identifier = StringProperty(Dcterms, 'identifier')
    represent = StringProperty(Meeting, 'represent')
