from ocd_backend import settings
from ocd_backend.app import celery_app
from ocd_backend.log import get_source_logger
from ocd_backend.transformers import BaseTransformer
from ocd_backend.models import *
from ocd_backend.utils.misc import deep_get, compare_insensitive

log = get_source_logger('ggm_meeting')


@celery_app.task(bind=True, base=BaseTransformer, autoretry_for=settings.AUTORETRY_EXCEPTIONS, retry_backoff=True)
def meeting_item(self, content_type, raw_item, canonical_iri, cached_path, **kwargs):
    original_item = self.deserialize_item(content_type, raw_item)
    self.source_definition = kwargs['source_definition']

    source_defaults = {
        'source': 'tweedekamer',
        'supplier': 'gegevensmagazijn',
        'canonical_iri': canonical_iri,
        'cached_path': cached_path,
    }

    meeting = Meeting(original_item['Id'], collection='meeting', **source_defaults)
    meeting.name = original_item.get('Onderwerp')
    meeting.start_date = original_item.get('Aanvangstijd')
    meeting.end_date = original_item.get('Eindtijd')
    meeting.location = deep_get(original_item, 'Reservering', 'Zaal', 'Naam')
    meeting.classification = original_item.get('Soort')
    meeting.organization = TopLevelOrganization('tweede-kamer',
                                                collection='organization',
                                                **source_defaults)
    meeting.organization.classification = 'Parliament'
    meeting.organization.name = 'Tweede Kamer'
    meeting.committee = Organization(original_item['Voortouwcommissie_Id'],
                                     collection='organization',
                                     **source_defaults)
    meeting.committee.name = original_item.get('Voortouwnaam')

    meeting.replaces = []
    for item in original_item.get('VervangenDoor', []):
        replaces = Meeting(item['Id'], collection='meeting', **source_defaults)
        replaces.name = item.get('Onderwerp')
        meeting.replaces.append(replaces)

    meeting.replaced_by = []
    for item in original_item.get('VervangenVanuit', []):
        replaced_by = Meeting(item['Id'], collection='meeting', **source_defaults)
        replaced_by.name = item.get('Onderwerp')
        meeting.replaced_by.append(replaced_by)

    meeting.attachment = []
    for document in original_item.get('Document', []):
        attachment = MediaObject(document['Id'], collection='attachment', **source_defaults)
        attachment.name = document.get('Onderwerp')
        attachment.original_url = deep_get(document, '#TK.DA.GGM.OData.Resource', 'target')
        attachment.identifier_url = 'ggm/resource/%s' % document['Id']
        attachment.last_discussed_at = document.get('Datum')
        attachment.upload_date = document.get('DatumRegistratie') or document.get('DatumOntvangst')
        attachment.date_modified = document.get('GewijzigdOp')
        attachment.size_in_bytes = document['ContentLength']
        attachment.content_type = document['ContentType']
        attachment.is_referenced_by = meeting
        attachment.creator = []
        for actor in document.get('DocumentActor', []):
            person = Person(actor['Persoon_Id'], collection='person', **source_defaults)
            person.name = actor.get('ActorNaam')
            attachment.creator.append(person)

        meeting.attachment.append(attachment)

    meeting.attendee = []
    meeting.absentee = []
    for actor in original_item.get('ActiviteitActor', []):
        if not actor.get('Persoon_Id'):
            continue

        attendee = Person(actor['Persoon_Id'], collection='person', **source_defaults)
        attendee.name = actor.get('ActorNaam')

        if compare_insensitive(actor.get('Relatie'), 'afgemeld'):
            meeting.absentee.append(attendee)
        else:
            meeting.attendee.append(attendee)

    meeting.agenda = []
    for agendapunt in original_item.get('Agendapunt', []):
        agenda_item = AgendaItem(agendapunt['Id'], collection='agenda_item', **source_defaults)
        agenda_item.name = agendapunt.get('Onderwerp')
        agenda_item.last_discussed_at = agendapunt.get('GewijzigdOp')
        agenda_item.start_date = agendapunt.get('Aanvangstijd') or meeting.start_date
        agenda_item.end_date = agendapunt.get('Eindtijd') or meeting.end_date
        agenda_item.position = agendapunt.get('Volgorde')
        agenda_item.parent = meeting

        agenda_item.attachment = []
        for document in agendapunt.get('Document', []):
            attachment = MediaObject(document['Id'], collection='attachment', **source_defaults)
            attachment.name = document.get('Onderwerp')
            attachment.original_url = deep_get(document, '#TK.DA.GGM.OData.Resource', 'target')
            attachment.identifier_url = 'ggm/resource/%s' % document['Id']
            attachment.last_discussed_at = document.get('Datum')
            attachment.upload_date = document.get('DatumRegistratie') or document.get('DatumOntvangst')
            attachment.date_modified = document.get('GewijzigdOp')
            attachment.size_in_bytes = document['ContentLength']
            attachment.content_type = document['ContentType']
            attachment.is_referenced_by = agenda_item
            attachment.creator = []
            for actor in document.get('DocumentActor', []):
                person = Person(actor['Persoon_Id'], collection='person', **source_defaults)
                person.name = actor.get('ActorNaam')
                attachment.creator.append(person)

            agenda_item.attachment.append(attachment)

        agenda_item.motion = []
        for besluit in agendapunt.get('Besluit', []):
            motion = Motion(besluit.get('Id'), collection='motion', **source_defaults)
            motion.name = deep_get(besluit, 'Zaak', 0, 'Onderwerp')
            motion.legislative_session = original_item.get('Vergaderjaar')
            motion.result = besluit.get('BesluitTekst')
            motion.is_referenced_by = agenda_item

            if besluit.get('BesluitSoort') != "[Vrij tekstveld / geen Parlisproces]":
                motion.classification = besluit.get('BesluitSoort')

            # todo: classifications should be IRI's
            if compare_insensitive(besluit.get('Status'), 'concept'):
                motion.status = 'concept'
            elif compare_insensitive(besluit.get('Status'), 'verwerken'):
                motion.status = 'unprocessed'
            elif compare_insensitive(besluit.get('Status'), 'voorstel'):
                motion.status = 'proposal'
            elif compare_insensitive(besluit.get('Status'), 'besluit'):
                motion.status = 'decision'

            motion.attachment = []
            for document in deep_get(besluit, 'Zaak', 0, 'Document') or []:
                attachment = MediaObject(document.get('Id'), collection='attachment', **source_defaults)
                attachment.name = document.get('Onderwerp')
                attachment.original_url = deep_get(document, '#TK.DA.GGM.OData.Resource', 'target')
                attachment.identifier_url = 'ggm/resource/%s' % document['Id']
                attachment.last_discussed_at = document.get('Datum')
                attachment.upload_date = document.get('DatumRegistratie') or document.get('DatumOntvangst') # 2014-02-05 16:02:55.813000+01:00
                attachment.date_modified = document.get('GewijzigdOp')
                attachment.size_in_bytes = document['ContentLength']
                attachment.content_type = document['ContentType']
                # todo add dossier as isReferencedBy
                attachment.is_referenced_by = motion
                attachment.creator = []
                for actor in document.get('DocumentActor', []):
                    person = Person(actor['Persoon_Id'], collection='person', **source_defaults)
                    person.name = actor.get('ActorNaam')
                    attachment.creator.append(person)

                attachment.enricher_task.append('ggm_motion_text')
                motion.attachment.append(attachment)

                motion.creator = []
                motion.cocreator = []
                for actor in document.get('DocumentActor', []):
                    # Skip if actor is a committee
                    if not actor.get('Persoon_Id'):
                        continue

                    membership = Membership(actor['Id'], collection='membership', **source_defaults)
                    membership.member = Person(actor['Persoon_Id'], collection='person', **source_defaults)
                    membership.member.name = actor.get('ActorNaam')
                    membership.role = actor.get('Functie')
                    if actor.get('Fractie_Id'):
                        membership.organization = Organization(actor.get('Fractie_Id'), collection='party', **source_defaults)
                        membership.organization.name = actor.get('ActorFractie')

                    if actor.get('Relatie') == 'Medeindiener':
                        motion.cocreator.append(membership)
                    else:
                        motion.creator.append(membership)

            if besluit.get('StemmingsSoort') and besluit.get('Stemming'):
                motion.vote_event = VoteEvent(besluit.get('Id'), collection='vote_event', **source_defaults)

                if compare_insensitive(besluit.get('BesluitTekst'), 'aangenomen'):
                    motion.vote_event.result = ResultPassed
                elif compare_insensitive(besluit.get('BesluitTekst'), 'verworpen'):
                    motion.vote_event.result = ResultFailed
                elif compare_insensitive(besluit.get('BesluitTekst'), 'aangehouden'):
                    motion.vote_event.result = ResultKept
                elif compare_insensitive(besluit.get('BesluitTekst'), 'uitgesteld'):
                    motion.vote_event.result = ResultPostponed
                elif compare_insensitive(besluit.get('BesluitTekst'), 'ingetrokken'):
                    motion.vote_event.result = ResultWithdrawn
                else:
                    continue

                motion.vote_event.legislative_session = original_item.get('Vergaderjaar')
                motion.vote_event.updated_at = original_item.get('GewijzigdOp')
                motion.vote_event.motion = motion

                motion.vote_event.votes = []
                for stemming in besluit.get('Stemming', []):
                    vote = Vote(stemming['Id'], collection='vote', **source_defaults)
                    if compare_insensitive(stemming.get('Soort'), 'voor'):
                        vote.option = VoteOptionYes
                    elif compare_insensitive(stemming.get('Soort'), 'tegen'):
                        vote.option = VoteOptionNo
                    elif compare_insensitive(stemming.get('Soort'), 'onthouding'):
                        vote.option = VoteOptionAbstain

                    vote.group = Organization(stemming.get('Fractie_Id'), collection='party', **source_defaults)
                    vote.group.name = stemming.get('ActorFractie')
                    vote.vote_event = motion.vote_event
                    vote.vote_event.start_date = agenda_item.start_date
                    vote.vote_event.end_date = agenda_item.end_date
                    motion.vote_event.votes.append(vote)

                    if stemming.get('Persoon_Id'):
                        vote.voter = Person(stemming.get('Persoon_Id'), collection='person', **source_defaults)
                        vote.voter.name = stemming.get('ActorName')

                    if besluit.get('StemmingsSoort') == 'Hoofdelijk':
                        vote.weight = 1
                    else:
                        vote.weight = stemming.get('FractieGrootte')

            agenda_item.motion.append(motion)

        meeting.agenda.append(agenda_item)

    meeting.save()
    return meeting
