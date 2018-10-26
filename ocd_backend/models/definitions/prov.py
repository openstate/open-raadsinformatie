"""The classes in this org module are derived from and described by:
http://www.w3.org/ns/prov#
"""
import owl
from ocd_backend.models.definitions import Prov


class Entity(Prov, owl.Thing):  # todo juiste superclass?
    pass
