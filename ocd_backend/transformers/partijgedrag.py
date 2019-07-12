from ocd_backend.transformers import BaseTransformer
from ocd_backend.models import Motion, Organization, VoteEvent, Vote, Person, VoteOption, VoteResult


class MotionItem(BaseTransformer):
    def transform(self):
        source_defaults = {
            'source': 'partijgedrag',
            'supplier': 'gegevensmagazijn',
            'collection': 'motion',
        }

        motion = Motion(self.original_item['identifier'], **source_defaults)
        motion.name = self.original_item.get('titel')
        motion.text = self.original_item.get('tekst')
        motion.date = self.original_item.get('issuedate')
        motion.legislative_session = self.original_item['jaar']
        motion.organization = Organization('TK', **source_defaults)

        if 'indieners' in self.original_item and len(self.original_item['indieners']) > 0:
            indiener_id, indiener_naam = self.original_item['indieners'][0]
            if not indiener_id:
                indiener_id = indiener_naam

            creator = Person(indiener_id, **source_defaults)
            creator.name = indiener_naam
            motion.creator = creator

        if 'indieners' in self.original_item and len(self.original_item['indieners']) > 1:
            motion.cocreator = list()
            for indiener_id, indiener_naam in self.original_item['indieners'][1:]:

                if not indiener_id:
                    indiener_id = indiener_naam

                cocreator = Person(indiener_id, **source_defaults)
                cocreator.name = indiener_naam
                motion.cocreator.append(cocreator)

        vote_event = VoteEvent(self.original_item['identifier'], **source_defaults)
        vote_event.start_date = self.original_item.get('issuedate')

        if self.original_item['uitslag']:
            vote_event.result = VoteResult.PASSED
        elif not self.original_item['uitslag']:
            vote_event.result = VoteResult.FAILED

        if 'votes' in self.original_item:
            votes = list()
            for vote_option, vote_option_parties in self.original_item['votes'].items():
                for vote_party in vote_option_parties:
                    vote = Vote()

                    if 'kamerlid' in vote_party:
                        voter = Person(vote_party['kamerlid'], **source_defaults)
                        voter.name = vote_party['kamerlid']
                        vote.voter = voter

                    group = Organization(vote_party['partij'], **source_defaults)
                    group.name = vote_party['partij']
                    vote.group = group

                    vote.weight = vote_party['aantal']

                    if vote_option == 'voor':
                        vote.option = VoteOption.OPTION_YES
                    elif vote_option == 'tegen':
                        vote.option = VoteOption.OPTION_NO
                    elif vote_option == 'afwezig':
                        vote.option = VoteOption.ABSENT

                    votes.append(vote)

            vote_event.votes = votes

        motion.vote_events = vote_event

        return motion
