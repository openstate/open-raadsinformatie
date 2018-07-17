"""The classes in this ontology are defined by Argu BV. More details, current
definitions and information can be found here:
https://argu.co/voc/mapping/

The purpose of this ontology is to define identifiers that are used by data
suppliers. This way, our data contains references to the original data in the
spirit of linked open data.
"""
from ocd_backend.models.model import Individual


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

