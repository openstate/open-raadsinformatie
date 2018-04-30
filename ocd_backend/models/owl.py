import govid

from owltology.model import ModelBase
from owltology.property import Relation
from .namespaces import OWL, META


class Thing(ModelBase):
    ori_identifier = govid.ori_identifier
    ggm_identifier = govid.ggm_identifier
    ibabs_identifier = govid.ibabs_identifier
    notubiz_identifier = govid.notubiz_identifier
    cbs_identifier = govid.cbs_identifier

    meta = Relation(META, 'meta')

    class Meta:
        namespace = OWL
