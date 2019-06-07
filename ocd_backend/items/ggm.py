# todo needs revision v1
# import re
# from hashlib import sha1
#
# import iso8601
# from lxml import etree
#
# from ocd_backend.extractors import HttpRequestMixin
# from ocd_backend.items import BaseItem
# from ocd_backend.log import get_source_logger
# from ocd_backend.models import *
# from ocd_backend.utils.api import FrontendAPIMixin
#
# log = get_source_logger('item')
#
#
# class GegevensmagazijnBaseItem(BaseItem, HttpRequestMixin, FrontendAPIMixin):
#     def _xpath(self, path):
#         if not hasattr(self, 'xpath'):
#             self.xpath = etree.XPathEvaluator(self.original_item)
#         return self.xpath(path, smart_strings=False)
#
#     def _get_current_permalink(self):
#         return u'%sEntiteiten/%s' % (self.source_definition['base_url'],
#                                      self.get_original_object_id())
#
#     def _get_resource_permalink(self, item_id):
#         return u'%sResources/%s' % (self.source_definition['base_url'], item_id)
#
#     def _get_party(self, party_id):
#         try:
#             results = self.api_request(
#                 self.source_definition['index_name'], 'organizations',
#                 classification='Party')
#
#             for x in results:
#                 if x.get('meta', {}).get('original_object_id') == party_id:
#                     return x
#         except:
#             pass
#         return
#
#     def get_original_object_id(self):
#         return unicode(self._xpath("string(@id)"))
#
#     def get_original_object_urls(self):
#         return {"xml": self._get_current_permalink()}
#
#     def get_rights(self):
#         return u'undefined'
#
#     @staticmethod
#     def get_index_data():
#         return {}
#
#     @staticmethod
#     def get_all_text():
#         text_items = []
#         return u' '.join(text_items)
#
#
# class EventItem(GegevensmagazijnBaseItem):
#     def get_combined_index_data(self):
#         combined_index_data = {}
#
#         current_permalink = self._get_current_permalink()
#
#         event = Event(self.get_original_object_id())
#         event.name = self._xpath("string(onderwerp)")
#         # combined_index_data['start_date'] = iso8601.parse_date(self._xpath("string(planning/begin)"))
#         # debug.log(iso8601.parse_date(self._xpath("string(planning/einde)")))
#         # combined_index_data['end_date'] = self._xpath("string(planning/einde)")
#         event.location = self._xpath("string(locatie)")
#         event.categories = u'event_item'
#
#         # try:
#         #     combined_index_data[AgendaItem.position] = int(self._xpath("number(volgorde)"))
#         # except:
#         #     pass
#
#         event.agenda = [
#             AgendaItem(item) for item in self._xpath("agendapunt/@id")
#         ]
#
#         event.attendee = [
#             Person(item.xpath("string(@id)"))
#             for item in self._xpath("deelnemer")
#         ]
#
#         event.absentee = [
#             Person(item.xpath("string(@id)"))
#             for item in self._xpath("afgemeld")
#         ]
#
#         event.motion = [
#             Motion(item.xpath("string(@id)"))
#             for item in self._xpath("besluit")
#         ]
#
#         event.organizer = [
#             Organization(item.xpath("string(name())"))
#             for item in self._xpath("kamers/*")
#         ]
#
#         # Status might be with or without a capital
#         if self._xpath("contains(status, 'itgevoerd')"):  # Uitgevoerd
#             event.eventStatus = EventStatusType.EventCompleted
#         elif self._xpath("contains(status, 'ervplaats')"):  # Verplaatst
#             event.eventStatus = EventStatusType.EventRescheduled  # u'postponed'
#         elif self._xpath("contains(status, 'epland')"):  # Gepland
#             event.eventStatus = EventStatusType.EventScheduled  # u'tentative'
#         elif self._xpath("contains(status, 'eannuleerd')"):  # Geannuleerd
#             event.eventStatus = EventStatusType.EventCancelled  # u'cancelled'
#
#         event.ggmIdentifier = self.get_original_object_id()
#         event.ggmVrsNummer = self._xpath("string(vrsNummer)")
#         event.ggmNummer = self._xpath("string(nummer)")
#
#         # try:
#         #     combined_index_data['organization'] = committees[
#         #         self.original_item['dmu']['id']]
#         # except KeyError:
#         #     pass
#
#         # combined_index_data['organization_id'] = unicode(
#         #     self.original_item['dmu']['id'])
#
#         combined_index_data['sources'] = [
#             {
#                 'url': current_permalink,
#                 'note': u''
#             }
#         ]
#
#         # if 'items' in self.original_item:
#         #     combined_index_data['children'] = [
#         #         self.get_meeting_id(mi) for mi in self.original_item['items']]
#
#         combined_index_data['sources'] = []
#
#         return event
#
#
# class MotionItem(GegevensmagazijnBaseItem):
#     def get_combined_index_data(self):
#         motion = Motion(self.get_original_object_id())
#         motion.name = self._xpath("string(onderwerp)")
#         motion.voteEvent = [
#             VoteEvent(self._xpath("string(@id)"))
#         ]
#
#         # log.debug("Motion orig:%s id:%s" % (self._xpath("string(@id)"),
#         #                                VoteEvent.get_object_id(
#         #                                self._xpath("string(@id)"))))
#
#         return motion
#
#
# class ZaakMotionItem(GegevensmagazijnBaseItem):
#     def _get_vote_event(self, object_id):
#         results = self.api_request_object(
#             self.source_definition['index_name'], "vote_events", object_id)
#         return results
#
#     def get_combined_index_data(self):
#         motion = None
#
#         soort = self._xpath("string(soort)")
#         if soort == "Motie":
#             motion = Motion(self.get_original_object_id())
#         elif soort == "Amendement":
#             motion = Amendment(self.get_original_object_id())
#         elif soort == "Wetgeving":
#             motion = Bill(self.get_original_object_id())
#         elif soort == "Initiatiefwetgeving":
#             motion = PrivateMembersBill(self.get_original_object_id())
#         elif soort == "Verzoekschrift":
#             motion = Petition(self.get_original_object_id())
#
#         motion.name = self._xpath("string(onderwerp)")
#         motion.dateSubmitted = iso8601.parse_date(self._xpath("string(gestartOp)"))
#         motion.publisher = Organization(self._xpath("string(organisatie)"))
#         motion.creator = Person(self._xpath("string(indiener/persoon/@ref)"))
#         motion.voteEvent = [VoteEvent(v) for v in self._xpath("besluit/@ref")]
#         motion.cocreator = [Person(p) for p in self._xpath("string(medeindiener/persoon/@ref)")]
#         motion.ggmNummer = self._xpath("string(nummer)")
#         motion.ggmVolgnummer = self._xpath("string(volgnummer)")
#         # combined_index_data['concluded'] = self._xpath("boolean(afgedaan)")
#
#         return motion
#
#
# class VoteEventItem(GegevensmagazijnBaseItem):
#     def get_combined_index_data(self):
#         vote_event = VoteEvent(self.get_original_object_id())
#         vote_event.motion = Motion(self._xpath("string(@id)"))
#
#         # combined_index_data[VoteEvent.identifier] = unicode(
#         #    self._xpath("string(../volgorde)"))
#
#         result = re.sub(r'[^ a-z]', '', self._xpath("string(slottekst)").lower())
#         if result == "aangenomen":
#             vote_event.result = Result.ResultPass
#         elif result == "verworpen":
#             vote_event.result = Result.ResultFail
#         elif result == "aangehouden":
#             vote_event.result = Result.ResultKept
#         elif result == "uitgesteld":
#             vote_event.result = Result.ResultPostponed
#         elif result == "ingetrokken":
#             vote_event.result = Result.ResultWithdrawn
#         elif result == "vervallen":
#             vote_event.result = Result.ResultExpired
#         elif result == "inbreng geleverd":
#             vote_event.result = Result.ResultDiscussed
#         elif result == "vrijgegeven":
#             vote_event.result = Result.ResultPublished
#         else:
#             log.warning("Result %s does not exists for: %s" % (result, self.original_item))
#
#         sub_events = self.source_definition['mapping']['vote_event']['sub_items']
#         vote_event.count = [Count(c) for c in self._xpath(sub_events['count'] + "/@id")]
#         vote_event.vote = [Vote(v) for v in self._xpath(sub_events['vote'] + "/@id")]
#
#         return vote_event
#
#
# class CountItem(GegevensmagazijnBaseItem):
#     def get_combined_index_data(self):
#         count = None
#
#         soort = unicode(self._xpath("string(soort)"))
#         if soort == "Voor":
#             count = YesCount(self.get_original_object_id())
#         elif soort == "Tegen":
#             count = NoCount(self.get_original_object_id())
#         elif soort == "Onthouding":
#             count = AbstainCount(self.get_original_object_id())
#         elif soort == "Niet deelgenomen":
#             count = AbsentCount(self.get_original_object_id())
#
#         # count.group = self._get_party(self._xpath("string(fractie/@ref)"))
#         count.group = Organization(self._xpath("string(fractie/@ref)"))
#         count.value = self._xpath("number(fractieGrootte)")
#
#         return count
#
#
# class VoteItem(GegevensmagazijnBaseItem):
#     def get_combined_index_data(self):
#         vote = Vote(self.get_original_object_id())
#
#         soort = unicode(self._xpath("string(soort)"))
#         if soort == "Voor":
#             vote.Vote = VoteOption.VoteOptionYes
#         elif soort == "Tegen":
#             combined_index_data[TYPE] = VoteOption.VoteOptionNo
#         elif soort == "Onthouding":
#             combined_index_data[TYPE] = VoteOption.VoteOptionAbstain
#         elif soort == "Niet deelgenomen":
#             combined_index_data[TYPE] = VoteOption.VoteOptionAbsent
#
#         # person = self._get_person(self._xpath("string(persoon/@ref)"))
#         # if person:
#         #     person.update({"@context": PersonItem.ld_context, "@type":
#         #         "http://www.w3.org/ns/person#Person"})
#         #     combined_index_data['group'] = person
#
#         return combined_index_data
#
#
# class PersonItem(GegevensmagazijnBaseItem):
#     def get_combined_index_data(self):
#         combined_index_data = dict()
#
#         combined_index_data[CONTEXT] = context
#         combined_index_data[ID] = unicode(
#             self.get_object_id())  # unicode(self.get_object_iri())
#         combined_index_data[TYPE] = Person.type
#         combined_index_data[HIDDEN] = self.source_definition['hidden']
#
#         # combined_index_data['honorific_prefix'] = unicode(self._xpath("string(/persoon/titels)"))
#         combined_index_data[Person.familyName] = unicode(
#             self._xpath("string(/persoon/achternaam)"))
#         combined_index_data[Person.givenName] = unicode(
#             self._xpath("string(/persoon/voornamen)"))
#         combined_index_data[Person.name] = u' '.join([x for x in [
#             self._xpath("string(/persoon/roepnaam)"),
#             self._xpath("string(/persoon/tussenvoegsel)"),
#             combined_index_data[Person.familyName]] if x != ''])
#
#         gender = self._xpath("string(/persoon/geslacht)")
#         if gender == 'man':
#             combined_index_data[Person.gender] = u"male"
#         elif gender == 'vrouw':
#             combined_index_data[Person.gender] = u"female"
#
#         if self._xpath("string(/persoon/geboortdatum)"):
#             combined_index_data[Person.birthDate] = iso8601.parse_date(
#                 self._xpath("string(/persoon/geboortdatum)"))
#         if self._xpath("string(/persoon/overlijdensdatum)"):
#             combined_index_data[Person.deathDate] = iso8601.parse_date(
#                 self._xpath("string(/persoon/overlijdensdatum)"))
#
#         combined_index_data[Person.nationalIdentity] = unicode(
#             self._xpath("string(/persoon/geboorteland)"))
#         combined_index_data[Person.email] = unicode(self._xpath(
#             "string(/persoon/contactinformatie[soort='E-mail']/waarde)"))
#         combined_index_data[Person.seeAlso] = [unicode(self._xpath(
#             "string(/persoon/contactinformatie[soort='Website']/waarde)"))]
#
#         image = self._xpath("string(/persoon/afbeelding/@ref)")
#         if image:
#             permalink = self._get_resource_permalink(image)
#             hashed_url = sha1(permalink).hexdigest()
#             combined_index_data['media_urls'] = [
#                 {
#                     "url": "/v0/resolve/%s" % hashed_url,
#                     "original_url": permalink
#                 }
#             ]
#
#         combined_index_data[ggmIdentifier] = self.get_original_object_id()
#         combined_index_data[oriIdentifier] = self.get_object_id()
#
#         # combined_index_data['memberships'] = [
#         #     {
#         #         'label': role,
#         #         'role': role,
#         #         'person_id': combined_index_data['id'],
#         #         'organization_id': council_id,
#         #         'organization': council_obj
#         #     }
#         # ]
#         return combined_index_data
#
#
# class DocumentItem(GegevensmagazijnBaseItem):
#     def get_combined_index_data(self):
#         combined_index_data = dict()
#
#         combined_index_data[CONTEXT] = context
#         combined_index_data[ID] = unicode(
#             self.get_object_id())  # unicode(self.get_object_iri())
#         combined_index_data[TYPE] = Attachment.type
#         combined_index_data[HIDDEN] = self.source_definition['hidden']
#
#         document = unicode(self._xpath("string(bestand/@ref)"))
#         if document:
#             combined_index_data['media_urls'] = [
#                 {
#                     "url": "/v0/resolve/",
#                     "note": "",
#                     "original_url": self._get_resource_permalink(document)
#                 }
#             ]
#
#         return combined_index_data
