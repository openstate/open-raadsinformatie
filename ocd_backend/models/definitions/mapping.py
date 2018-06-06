"""The classes in this ontology are defined by Argu BV. More details, current
definitions and information can be found here:
https://argu.co/voc/mapping/

The purpose of this ontology is to define identifiers that are used by data
suppliers. This way, our data contains references to the original data in the
spirit of linked open data.
"""
from ..model import Individual, ModelBase


class OriIdentifier(Individual):
    class Meta:
        verbose_name = 'ori/identifier'


class RunIdentifier(Individual):
    class Meta:
        verbose_name = 'ori/meta/runIdentifier'


class MetadataIdentifier(Individual):
    class Meta:
        verbose_name = 'ori/meta/metadataIdentifier'


class IbabsIdentifier(Individual):
    class Meta:
        verbose_name = 'ibabs/identifier'


class NotubizIdentifier(Individual):
    class Meta:
        verbose_name = 'notubiz/identifier'


class CbsIdentifier(Individual):
    class Meta:
        verbose_name = 'cbs/identifier'


class AlmanakOrganizationName(Individual):
    class Meta:
        verbose_name = 'almanak/organizationName'


class GGMIdentifier(Individual):
    class Meta:
        verbose_name = 'ggm/identifier'


class GGMVrsNummer(Individual):
    class Meta:
        verbose_name = 'ggm/vrsnummer'


class GGMNummer(Individual):
    class Meta:
        verbose_name = 'ggm/nummer'


class GGMVolgnummer(Individual):
    class Meta:
        verbose_name = 'ggm/volgnummer'


# ori_identifier = Individual(EXT, 'ori/identifier')
# ibabs_identifier = IbabsIdentifier(EXT, 'ibabs/identifier')
# notubiz_identifier = Individual(EXT, 'notubiz/identifier')
# cbs_identifier = Individual(EXT, 'cbs/identifier')
# ggm_identifier = Individual(EXT, 'ggm/identifier')
# ggm_vrsnummer = Individual(EXT, 'ggm/vrsNummer')
# ggm_nummer = Individual(EXT, 'ggm/nummer')
# ggm_volgnummer = Individual(EXT, 'ggm/volgNummer')
