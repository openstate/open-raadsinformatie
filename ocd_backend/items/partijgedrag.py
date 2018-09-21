from ocd_backend.items import BaseItem
from ocd_backend.models import Motion, Organization, VoteEvent, ResultPass,\
    ResultFail, Vote, Person, VoteOptionYes, VoteOptionNo, VoteOptionAbsent


class PartijgedragMotion(BaseItem):
    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        source_defaults = {
            'source': 'partijgedrag',
            'source_id_key': 'identifier',
            'organization': 'ggm',
        }

        motion = Motion(self.original_item['identifier'], **source_defaults)
        motion.name = self.original_item.get('titel')
        motion.text = self.original_item.get('tekst')
        motion.date = self.original_item.get('issuedate')
        motion.legislative_session = self.original_item['jaar']
        motion.organization = Organization('TK', **source_defaults)

        if 'indieners' in self.original_item and len(self.original_item['indieners']) > 0:
            indiener_id, indiener_naam = self.original_item['indieners'][0]
            creator = Person(indiener_id, **source_defaults)
            creator.name = indiener_naam
            motion.creator = creator

        if 'indieners' in self.original_item and len(self.original_item['indieners']) > 1:
            motion.cocreator = list()
            for indiener_id, indiener_naam in self.original_item['indieners'][1:]:
                cocreator = Person(indiener_id, **source_defaults)
                cocreator.name = indiener_naam
                motion.cocreator.append(cocreator)

        vote_event = VoteEvent(self.original_item['identifier'], **source_defaults)

        if self.original_item['uitslag']:
            vote_event.result = ResultPass()
        elif not self.original_item['uitslag']:
            vote_event.result = ResultFail()

        if 'votes' in self.original_item:
            votes = list()
            for vote_option, vote_option_parties in self.original_item['votes'].items():
                for vote_party in vote_option_parties:
                    vote = Vote()

                    if 'kamerlid' in vote_party:
                        vote.voter = Person(vote_party['kamerlid'], **source_defaults)

                    vote.group = Organization(vote_party['partij'], **source_defaults)
                    vote.weight = vote_party['aantal']

                    if vote_option == 'voor':
                        vote.option = VoteOptionYes()
                    elif vote_option == 'tegen':
                        vote.option = VoteOptionNo()
                    elif vote_option == 'afwezig':
                        vote.option = VoteOptionAbsent()

                    votes.append(vote)

            vote_event.votes = votes

        motion.vote_events = vote_event

        return motion
