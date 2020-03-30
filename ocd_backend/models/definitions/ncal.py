"""The classes in this ncal module are derived from and described by:
http://www.semanticdesktop.org/ontologies/2007/04/02/ncal#
"""

from ocd_backend.models.definitions import owl
from ocd_backend.models.definitions import Ncal


class Category(Ncal, owl.Thing):
    pass
