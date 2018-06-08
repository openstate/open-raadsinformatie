"""The classes in this org module are derived from and described by:
https://www.w3.org/TR/2013/REC-prov-o-20130430/#
"""
import owl
from ocd_backend.models.definitions import Prov


class Entity(Prov, owl.Thing):  # todo juiste superclass?
    pass
