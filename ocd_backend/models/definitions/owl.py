"""The classes in this owl module are derived from and described by:
http://www.w3.org/2002/07/owl#
"""

from ocd_backend.models.definitions import Meta, Dcterms, Meeting, Ncal, Owl, Vcard
from ocd_backend.models.model import Model
from ocd_backend.models.properties import Relation, StringProperty, ArrayProperty


class Thing(Owl, Model):
    classification = ArrayProperty(Ncal, 'categories')  # todo fix with popolo
    meta = Relation(Meta, 'meta')
    canonical_iri = StringProperty(Meta, 'canonical_iri')
    canonical_id = StringProperty(Meta, 'canonical_id')
    # has_organization_name is used to set the municipality or province ID on every item (see issue #141)
    has_organization_name = Relation(Vcard, 'hasOrganizationName')


class Identifier(Thing):
    identifier = StringProperty(Dcterms, 'identifier')
    represent = StringProperty(Meeting, 'represent')
