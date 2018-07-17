"""The classes in this ontology are defined by Argu BV. More details, current
definitions and information can be found here:
https://argu.co/voc/mapping/

The purpose of this ontology is to define identifiers that are used by data
suppliers. This way, our data contains references to the original data in the
spirit of linked open data.
"""
from ocd_backend.models.definitions import Mapping
from ocd_backend.models.model import Individual


class OriIdentifier(Mapping, Individual):
    class Meta:
        verbose_name = 'ori/identifier'


class RunIdentifier(Mapping, Individual):
    class Meta:
        verbose_name = 'ori/meta/runIdentifier'


class MetadataIdentifier(Mapping, Individual):
    class Meta:
        verbose_name = 'ori/meta/metadataIdentifier'


class IbabsIdentifier(Mapping, Individual):
    class Meta:
        verbose_name = 'ibabs/identifier'


class NotubizIdentifier(Mapping, Individual):
    class Meta:
        verbose_name = 'notubiz/identifier'


class CbsIdentifier(Mapping, Individual):
    class Meta:
        verbose_name = 'cbs/identifier'


class AlmanakOrganizationName(Mapping, Individual):
    class Meta:
        verbose_name = 'almanak/organizationName'


class GGMIdentifier(Mapping, Individual):
    class Meta:
        verbose_name = 'ggm/identifier'


class GGMVrsNummer(Mapping, Individual):
    class Meta:
        verbose_name = 'ggm/vrsnummer'


class GGMNummer(Mapping, Individual):
    class Meta:
        verbose_name = 'ggm/nummer'


class GGMVolgnummer(Mapping, Individual):
    class Meta:
        verbose_name = 'ggm/volgnummer'
