import govid

from owltology.model import ModelBase
from owltology.property import Property
from .namespaces import OWL, COUNCIL


class Thing(ModelBase):
    NAMESPACE = OWL

    # Optional local identifier which doesn't have to be an URI
    identifier = 'dcterms:identifier'

    _hidden = Property(COUNCIL, 'hidden')  # _hidden is required by ori for filtering

    ggmIdentifier = govid.ggmIdentifier
    oriIdentifier = govid.oriIdentifier
