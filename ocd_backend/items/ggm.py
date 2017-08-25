import re
from hashlib import sha1

import iso8601

from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.items import BaseItem
from ocd_backend.models import *
from ocd_backend.utils.api import FrontendAPIMixin


class GegevensmagazijnBaseItem(BaseItem, HttpRequestMixin, FrontendAPIMixin):

    def _xpath(self, path):
        return self.original_item.xpath(path)

    def _get_current_permalink(self):
        return u'%sEntiteiten/%s' % (self.source_definition['base_url'],
                                     self.get_object_id())

    def _get_resource_permalink(self, item_id):
        return u'%sResources/%s' % (self.source_definition['base_url'], item_id)

    def _get_party(self, party_id):
        try:
            results = self.api_request(
                self.source_definition['index_name'], 'organizations',
                classification='Party')

            for x in results:
                if x.get('meta', {}).get('original_object_id') == party_id:
                    return x
        except:
            pass
        return

    def get_object_iri(self):
        return u"http://id.openraadsinformatie.nl/%s" % self.get_object_id()

    def get_original_object_id(self):
        return unicode(self._xpath("string(@id)"))

    def get_original_object_urls(self):
        return {"xml": self._get_current_permalink()}

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_index_data(self):
        return {}

    def get_all_text(self):
        text_items = []
        return u' '.join(text_items)


class EventItem(GegevensmagazijnBaseItem):

    def get_combined_index_data(self):
        combined_index_data = {}

        current_permalink = self._get_current_permalink()

        combined_index_data[CONTEXT] = context
        combined_index_data[ID] = unicode(
            self.get_object_id())  # unicode(self.get_object_iri())
        combined_index_data[TYPE] = Event.type
        combined_index_data[HIDDEN] = self.source_definition['hidden']

        combined_index_data[Event.name] = unicode(
            self._xpath("string(onderwerp)"))
        # combined_index_data['start_date'] = iso8601.parse_date(self._xpath("string(planning/begin)"))
        # print iso8601.parse_date(self._xpath("string(planning/einde)"))
        # combined_index_data['end_date'] = self._xpath("string(planning/einde)")
        combined_index_data[Event.location] = unicode(
            self._xpath("string(locatie)"))
        combined_index_data[Event.categories] = u'event_item'

        combined_index_data[AgendaItem.position] = int(self._xpath("volgorde"))

        combined_index_data[Event.hasAgendaItem] = [
            u'../event_items/%s' % self.get_object_id(
                item.xpath("string(@id)"), "event_items") for item in
            self._xpath("agendapunt")
        ]

        combined_index_data[Event.attendee] = [
            u'../persons/%s' %
            self.get_object_id(item.xpath("string(@id)"), "persons")
            for item in self._xpath("deelnemer")
        ]

        combined_index_data[Event.absentee] = [
            u'../persons/%s' %
            self.get_object_id(item.xpath("string(@id)"), "persons")
            for item in self._xpath("afgemeld")
        ]

        combined_index_data[Event.motion] = [
            u'../motions/%s' %
            self.get_object_id(item.xpath("string(@id)"), "motions")
            for item in self._xpath("besluit")
        ]

        combined_index_data[Event.organizer] = [{
            ID: item.xpath("string(@id)"),
            TYPE: Organization.type,
            Organization.name: item.xpath("string(name())")}
            for item in self._xpath("kamers/*")]

        # Status might be with or without a capital
        if self._xpath("contains(status, 'itgevoerd')"):  # Uitgevoerd
            combined_index_data[
                Event.eventStatus] = EventStatusType.EventCompleted
        elif self._xpath("contains(status, 'ervplaats')"):  # Verplaatst
            combined_index_data[
                Event.eventStatus] = EventStatusType.EventRescheduled  # u'postponed'
        elif self._xpath("contains(status, 'epland')"):  # Gepland
            combined_index_data[
                Event.eventStatus] = EventStatusType.EventScheduled  # u'tentative'
        elif self._xpath("contains(status, 'eannuleerd')"):  # Geannuleerd
            combined_index_data[
                Event.eventStatus] = EventStatusType.EventCancelled  # u'cancelled'

        combined_index_data[ggmIdentifier] = self.get_original_object_id()
        combined_index_data[ggmVrsNummer] = self._xpath(
            "string(vrsNummer)")
        combined_index_data[ggmNummer] = self._xpath(
            "string(nummer)")
        combined_index_data[oriIdentifier] = self.get_object_id()

        # try:
        #     combined_index_data['organization'] = committees[
        #         self.original_item['dmu']['id']]
        # except KeyError:
        #     pass

        # combined_index_data['organization_id'] = unicode(
        #     self.original_item['dmu']['id'])

        combined_index_data['sources'] = [
            {
                'url': current_permalink,
                'note': u''
            }
        ]

        # if 'items' in self.original_item:
        #     combined_index_data['children'] = [
        #         self.get_meeting_id(mi) for mi in self.original_item['items']]

        combined_index_data['sources'] = []

        return combined_index_data


class MotionItem(GegevensmagazijnBaseItem):

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data[CONTEXT] = context
        combined_index_data[ID] = unicode(
            self.get_object_id())  # unicode(self.get_object_iri())
        combined_index_data[TYPE] = Motion.type
        combined_index_data[HIDDEN] = self.source_definition['hidden']
        combined_index_data[Motion.name] = unicode(
            self._xpath("string(onderwerp)"))

        combined_index_data[Motion.voteEvent] = [
            u"../vote_events/%s" % (
                self.get_object_id(self._xpath("string(@id)"), "vote_events"))]

        print "Motion orig:%s id:%s" % (self._xpath("string(@id)"),
                                        self.get_object_id(
                                            self._xpath("string(@id)"),
                                            "vote_events"))

        return combined_index_data


class ZaakMotionItem(GegevensmagazijnBaseItem):
    def _get_vote_event(self, object_id):
        results = self.api_request_object(
            self.source_definition['index_name'], "vote_events", object_id)
        return results

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data[CONTEXT] = context
        combined_index_data[ID] = unicode(
            self.get_object_id())  # unicode(self.get_object_iri())
        combined_index_data[HIDDEN] = self.source_definition['hidden']

        combined_index_data[Motion.name] = unicode(
            self._xpath("string(onderwerp)"))

        soort = self._xpath("string(soort)")
        if soort == "Motie":
            combined_index_data[TYPE] = Motion.type  # u"Motion"
        elif soort == "Amendement":
            combined_index_data[TYPE] = Amendment.type  # u"Amendment"
        elif soort == "Wetgeving":
            combined_index_data[TYPE] = Bill.type  # u"Legislation"
        elif soort == "Initiatiefwetgeving":
            combined_index_data[
                TYPE] = PrivateMembersBill.type  # u"Private members's bill"
        elif soort == "Verzoekschrift":
            combined_index_data[TYPE] = Petition.type  # u"Petition"

        combined_index_data[Motion.dateSubmitted] = iso8601.parse_date(
            self._xpath("string(gestartOp)"))

        combined_index_data[Motion.voteEvent] = []
        for vote_event in self._xpath("besluit/@ref"):
            # print "VOTE_EVENT_REF: %s" % vote_event
            # print "VOTE_EVENT_ID: %s" % get_vote_event_id(vote_event)
            vote_event = self._get_vote_event(
                self.get_object_id(vote_event, "vote_events"))
            # print "VOTE_EVENT %s" % type(vote_event)
            if vote_event:
                combined_index_data[Motion.voteEvent].append(vote_event)

        # combined_index_data['vote_events'] = [
        #     vote_event for vote_event in self._xpath("besluit/")
        # ]


        # combined_index_data['concluded'] = self._xpath("boolean(afgedaan)")

        # combined_index_data['submitter'] = self._xpath(
        #    "string(indiener/persoon/@ref)")

        # combined_index_data['identifiers'] = [
        #     {
        #         '@type': 'Identifier',
        #         'value': unicode(self._xpath("string(volgnummer)")),
        #         'identifierScheme': u'Volgnummer'
        #     },
        #     {
        #         '@type': 'Identifier',
        #         'value': unicode(self._xpath("string(nummer)")),
        #         'identifierScheme': u'Nummer'
        #     }
        # ]

        return combined_index_data


class VoteEventItem(GegevensmagazijnBaseItem):

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data[CONTEXT] = context
        combined_index_data[ID] = unicode(
            self.get_object_id())  # unicode(self.get_object_iri())
        combined_index_data[TYPE] = VoteEvent.type
        combined_index_data[HIDDEN] = self.source_definition['hidden']

        combined_index_data[
            VoteEvent.motion] = u"../motions/%s" % self.get_object_id(
            self._xpath("string(@id)"), "motions")
        combined_index_data[VoteEvent.identifier] = unicode(
            self._xpath("string(../volgorde)"))

        # print "id:%s orig_id:%s" % (combined_index_data['id'], self._xpath("string(@id)"))
        # print "motion:%s" % get_vote_event_id(self._xpath("string(@id)"))

        result = re.sub(r'[^ a-z]', '', self._xpath("string(""slottekst)").lower())
        if result == "aangenomen":
            combined_index_data[VoteEvent.result] = Result.ResultPass
        elif result == "verworpen":
            combined_index_data[VoteEvent.result] = Result.ResultFail
        elif result == "aangehouden":
            combined_index_data[VoteEvent.result] = Result.ResultKept
        elif result == "uitgesteld":
            combined_index_data[VoteEvent.result] = Result.ResultPostponed
        elif result == "ingetrokken":
            combined_index_data[VoteEvent.result] = Result.ResultWithdrawn
        elif result == "vervallen":
            combined_index_data[VoteEvent.result] = Result.ResultExpired
        elif result == "inbreng geleverd":
            combined_index_data[VoteEvent.result] = Result.ResultDiscussed
        elif result == "vrijgegeven":
            combined_index_data[VoteEvent.result] = Result.ResultPublished
        else:
            print "Result %s does not exists for: %s" % (result, self.original_item)

        sub_events = self.source_definition['mapping']['vote_event']['sub_items']

        combined_index_data[VoteEvent.count] = [
            u"../counts/%s" % (self.get_object_id(x, "counts")) for x in
            self._xpath(sub_events['count'] + "/@id")]
        combined_index_data[VoteEvent.vote] = [
            u"../votes/%s" % (self.get_object_id(x, "votes")) for x in
            self._xpath(sub_events['vote'] + "/@id")]

        return combined_index_data


class CountItem(GegevensmagazijnBaseItem):

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data[CONTEXT] = context
        combined_index_data[ID] = unicode(
            self.get_object_id())  # unicode(self.get_object_iri())
        combined_index_data[HIDDEN] = self.source_definition['hidden']

        soort = unicode(self._xpath("string(soort)"))
        if soort == "Voor":
            combined_index_data[TYPE] = YesCount.type
        elif soort == "Tegen":
            combined_index_data[TYPE] = NoCount.type
        elif soort == "Onthouding":
            combined_index_data[TYPE] = AbstainCount.type
        elif soort == "Niet deelgenomen":
            combined_index_data[TYPE] = AbsentCount.type

        party = self._get_party(self._xpath("string(fractie/@ref)"))
        if party:
            combined_index_data[Count.group] = party

        combined_index_data[Count.value] = int(self._xpath("number("
                                                       "fractieGrootte)"))

        return combined_index_data


class VoteItem(GegevensmagazijnBaseItem):

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data[CONTEXT] = context
        combined_index_data[ID] = unicode(self.get_object_id())
        combined_index_data[HIDDEN] = self.source_definition['hidden']

        soort = unicode(self._xpath("string(soort)"))
        if soort == "Voor":
            combined_index_data[TYPE] = VoteOption.VoteOptionYes
        elif soort == "Tegen":
            combined_index_data[TYPE] = VoteOption.VoteOptionNo
        elif soort == "Onthouding":
            combined_index_data[TYPE] = VoteOption.VoteOptionAbstain
        elif soort == "Niet deelgenomen":
            combined_index_data[TYPE] = VoteOption.VoteOptionAbsent

        # person = self._get_person(self._xpath("string(persoon/@ref)"))
        # if person:
        #     person.update({"@context": PersonItem.ld_context, "@type":
        #         "http://www.w3.org/ns/person#Person"})
        #     combined_index_data['group'] = person

        return combined_index_data


class PersonItem(GegevensmagazijnBaseItem):

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data[CONTEXT] = context
        combined_index_data[ID] = unicode(
            self.get_object_id())  # unicode(self.get_object_iri())
        combined_index_data[TYPE] = Person.type
        combined_index_data[HIDDEN] = self.source_definition['hidden']

        # combined_index_data['honorific_prefix'] = unicode(self._xpath("string(/persoon/titels)"))
        combined_index_data[Person.familyName] = unicode(
            self._xpath("string(/persoon/achternaam)"))
        combined_index_data[Person.givenName] = unicode(
            self._xpath("string(/persoon/voornamen)"))
        combined_index_data[Person.name] = u' '.join([x for x in [
            self._xpath("string(/persoon/roepnaam)"),
            self._xpath("string(/persoon/tussenvoegsel)"),
            combined_index_data[Person.familyName]] if x != ''])

        gender = self._xpath("string(/persoon/geslacht)")
        if gender == 'man':
            combined_index_data[Person.gender] = u"male"
        elif gender == 'vrouw':
            combined_index_data[Person.gender] = u"female"

        if self._xpath("string(/persoon/geboortdatum)"):
            combined_index_data[Person.birthDate] = iso8601.parse_date(
                self._xpath("string(/persoon/geboortdatum)"))
        if self._xpath("string(/persoon/overlijdensdatum)"):
            combined_index_data[Person.deathDate] = iso8601.parse_date(
                self._xpath("string(/persoon/overlijdensdatum)"))

        combined_index_data[Person.nationalIdentity] = unicode(
            self._xpath("string(/persoon/geboorteland)"))
        combined_index_data[Person.email] = unicode(self._xpath(
            "string(/persoon/contactinformatie[soort='E-mail']/waarde)"))
        combined_index_data[Person.seeAlso] = [unicode(self._xpath(
            "string(/persoon/contactinformatie[soort='Website']/waarde)"))]

        image = self._xpath("string(/persoon/afbeelding/@ref)")
        if image:
            permalink = self._get_resource_permalink(image)
            hashed_url = sha1(permalink).hexdigest()
            combined_index_data['media_urls'] = [
                {
                    "url": "/v0/resolve/%s" % hashed_url,
                    "original_url": permalink
                }
            ]

        combined_index_data[ggmIdentifier] = self.get_original_object_id()
        combined_index_data[oriIdentifier] = self.get_object_id()

        # combined_index_data['memberships'] = [
        #     {
        #         'label': role,
        #         'role': role,
        #         'person_id': combined_index_data['id'],
        #         'organization_id': council_id,
        #         'organization': council_obj
        #     }
        # ]
        return combined_index_data


class DocumentItem(GegevensmagazijnBaseItem):

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data[CONTEXT] = context
        combined_index_data[ID] = unicode(
            self.get_object_id())  # unicode(self.get_object_iri())
        combined_index_data[TYPE] = Attachment.type
        combined_index_data[HIDDEN] = self.source_definition['hidden']

        document = unicode(self._xpath("string(bestand/@ref)"))
        if document:
            combined_index_data['media_urls'] = [
                {
                    "url": "/v0/resolve/",
                    "note": "",
                    "original_url": self._get_resource_permalink(document)
                }
            ]

        return combined_index_data
