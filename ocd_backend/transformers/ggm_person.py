from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.transformers import BaseTransformer
from ocd_backend.models import *
from ocd_backend.utils.misc import deep_get, compare_insensitive

log = get_source_logger('ggm_person')


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def person_item(self, content_type, raw_item, canonical_iri, cached_path, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    source_defaults = {
        'source': 'tweedekamer',
        'supplier': 'gegevensmagazijn',
        'canonical_iri': canonical_iri,
        'cached_path': cached_path,
    }

    if original_item.get('Verwijderd') is None:

        return

    person = Person(original_item['Id'], collection='person', **source_defaults)
    person.initials = original_item.get('Initialen')
    person.nickname = original_item.get('Roepnaam')
    person.given_name = original_item.get('Voornamen')
    person.additional_name = original_item.get('Tussenvoegsel')
    person.family_name = original_item.get('Achternaam')
    person.name = ' '.join(x for x in [person.nickname, person.additional_name, person.family_name] if x)
    person.birth_date = original_item.get('Geboortedatum')
    person.summary = original_item.get('Functie')
    person.death_date = original_item.get('Overlijdensdatum')
    person.home_location = original_item.get('Woonplaats')
    person.birth_place = original_item.get('Geboorteplaats')
    if original_item.get('Geboorteland'):
        person.birth_place = '{}, {}'.format(person.birth_place, original_item.get('Geboorteland'))

    if compare_insensitive(original_item.get('Geslacht'), 'man'):
        person.gender = 'male'
    elif compare_insensitive(original_item.get('Geslacht'), 'vrouw'):
        person.gender = 'female'

    titles = original_item.get('Titels')
    if titles and titles[-1:] == '.':
        person.honorific_prefix = titles
    elif titles:
        person.honorific_suffix = titles

    image_url = deep_get(original_item, '#TK.DA.GGM.OData.Resource', 'target')
    if image_url:
        person.image = ImageObject(original_item.get('Id'), collection='image', **source_defaults)
        person.image.original_url = image_url
        person.image.identifier_url = 'ggm/resource/%s' % original_item['Id']
        person.image.date_modified = original_item.get('GewijzigdOp')
        person.image.size_in_bytes = original_item.get('ContentLength')
        person.image.content_type = original_item.get('ContentType')
        person.image.is_referenced_by = person

    for contact_informatie in original_item.get('PersoonContactinformatie', []):
        if contact_informatie.get('Soort') == 'Website':
            person.links = contact_informatie.get('Waarde')
        elif contact_informatie.get('Soort') == 'E-mail':
            person.email = contact_informatie.get('Waarde')

    person.member_of = []
    for zetel in original_item.get('FractieZetelPersoon'):
        membership = Membership(zetel['Id'], collection='membership', **source_defaults)
        membership.member = person
        membership.label = 'Fractielid'
        membership.role = zetel.get('Functie')
        membership.start_date = zetel.get('Van')
        membership.end_date = zetel.get('TotEnMet')

        fractie_id = deep_get(zetel, 'FractieZetel', 'Fractie_Id')
        if fractie_id:
            membership.organization = Organization(fractie_id, collection='party', **source_defaults)
            membership.organization.name = deep_get(zetel, 'FractieZetel', 'Fractie', 'NaamNL')

        person.member_of.append(membership)

    for commissie_zetel in original_item.get('CommissieZetelVastPersoon'):
        membership = Membership(commissie_zetel['Id'], collection='membership', **source_defaults)
        membership.member = person
        membership.label = 'Commissielid'
        membership.role = commissie_zetel.get('Functie')
        membership.start_date = commissie_zetel.get('Van')
        membership.end_date = commissie_zetel.get('TotEnMet')

        commissie_id = deep_get(commissie_zetel, 'CommissieZetel', 'Commissie_Id')
        if commissie_id:
            membership.organization = Organization(commissie_id, collection='committee', **source_defaults)
            membership.organization.name = deep_get(commissie_zetel, 'CommissieZetel', 'Commissie', 'NaamNL')

        person.member_of.append(membership)

    person.save()
    return person
