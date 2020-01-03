from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.transformers import BaseTransformer
from ocd_backend.models import *
from ocd_backend.utils.misc import deep_get
from ocd_backend.models.misc import Url

log = get_source_logger('ggm_committee')


ggm_feed_entiteiten = 'https://gegevensmagazijn.tweedekamer.nl/SyncFeed/2.0/Entiteiten'


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def committee_item(self, content_type, raw_item, canonical_iri, cached_path, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    source_defaults = {
        'source': 'tweedekamer',
        'supplier': 'gegevensmagazijn',
        'canonical_iri': lambda model: Url('%s/%s') % (ggm_feed_entiteiten, model.canonical_id),
        'cached_path': cached_path,
    }

    committee = Committee(original_item['Id'], collection='committee', **source_defaults)
    committee.name = original_item.get('NaamNL') or original_item.get('NaamWebNL') \
        or original_item.get('NaamEN') or original_item.get('NaamWebEN')
    committee.founding_date = original_item.get('DatumActief')
    committee.dissolution_date = original_item.get('DatumInactief')
    committee.alt_label = original_item.get('Afkorting')
    committee.classification = original_item.get('Soort') or original_item.get('Inhoudsopgave')

    for contact_informatie in original_item.get('PersoonContactinformatie', []):
        if contact_informatie.get('Soort') == 'E-mail':
            committee.email = contact_informatie.get('Waarde')

    committee.has_member = []
    for zetel in original_item.get('CommissieZetel', []):
        persoon = deep_get(zetel, 'CommissieZetelVastPersoon', 0, 'Persoon')
        if not persoon or not persoon.get('Id'):
            persoon = deep_get(zetel, 'CommissieZetelVervangerPersoon', 0, 'Persoon')
            if not persoon or not persoon.get('Id'):
                continue

        membership = Membership(zetel['Id'], collection='membership', **source_defaults)
        membership.label = 'Commissielid'
        membership.role = zetel.get('Functie')
        membership.start_date = zetel.get('Van')
        membership.end_date = zetel.get('TotEnMet')
        membership.organization = committee

        person = Person(persoon['Id'], collection='person', **source_defaults)
        person.name = ' '.join(x for x in [persoon.get('Roepnaam'), persoon.get('Tussenvoegsel'), persoon.get('Achternaam')] if x)
        membership.member = person

        committee.has_member.append(membership)

    committee.save()
    return committee
