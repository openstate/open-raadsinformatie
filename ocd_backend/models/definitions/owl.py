import govid

from ..model import ModelBase
from ..property import InlineRelation
from .namespaces import OWL, META


class Thing(ModelBase):
    ori_identifier = govid.ori_identifier
    ggm_identifier = govid.ggm_identifier
    ibabs_identifier = govid.ibabs_identifier
    notubiz_identifier = govid.notubiz_identifier
    cbs_identifier = govid.cbs_identifier

    meta = InlineRelation(META, 'meta')

    class Meta:
        namespace = OWL
