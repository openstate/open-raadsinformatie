"""The classes in this owl module are derived from and described by:
http://www.w3.org/2002/07/owl#
"""

from ocd_backend.models.definitions import Dcterms, Meeting, Ncal, Owl, Vcard, Prov
from ocd_backend.models.model import Model
from ocd_backend.models.properties import Relation, StringProperty, ArrayProperty, NestedProperty


class Thing(Owl, Model):
    classification = ArrayProperty(Ncal, 'categories')  # todo fix with popolo
    was_generated_by = NestedProperty(Prov, 'wasGeneratedBy')
    # has_organization_name is used to set the municipality or province ID on every item (see issue #141)
    has_organization_name = Relation(Vcard, 'hasOrganizationName')


class Identifier(Thing):
    identifier = StringProperty(Dcterms, 'identifier')
    represent = StringProperty(Meeting, 'represent')
