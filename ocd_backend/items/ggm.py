from hashlib import sha1
import iso8601
import re

from ocd_backend.items.popolo import EventItem, OrganisationItem, \
    MotionItem, PersonItem, VotingEventItem, VoteItem, CountItem, PopoloBaseItem
from ocd_backend.extractors import HttpRequestMixin
from ocd_backend.utils.api import FrontendAPIMixin


def get_motion_id(item_id):
    hash_content = u'motion-%s' % item_id
    return unicode(sha1(hash_content.decode('utf8')).hexdigest())


def get_vote_event_id(item_id):
    hash_content = u'vote-event-%s' % item_id
    return unicode(sha1(hash_content.decode('utf8')).hexdigest())


def get_count_id(item_id):
    hash_content = u'count-%s' % item_id
    return unicode(sha1(hash_content.decode('utf8')).hexdigest())


def get_vote_id(item_id):
    hash_content = u'vote-%s' % item_id
    return unicode(sha1(hash_content.decode('utf8')).hexdigest())


class GegevensmagazijnBaseItem(HttpRequestMixin, FrontendAPIMixin):

    def _xpath(self, path):
        return self.original_item.xpath(path)

    def _get_current_permalink(self):
        return u'%sEntiteiten/%s' % (self.source_definition['base_url'],
                                     self.get_object_id())

    def _get_resource_permalink(self, item_id):
        return u'%sResources/%s' % (self.source_definition['base_url'], item_id)

    def _get_party(self, party_id):
        results = self.api_request(
            self.source_definition['index_name'], 'organizations',
            classification='Party')

        for x in results:
            if x.get('meta', {}).get('original_object_id') == party_id:
                return x
        return

    def get_object_id(self):
        raise NotImplementedError

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


class Meeting(GegevensmagazijnBaseItem, EventItem):

    def get_object_id(self):
        return self.get_meeting_id()

    def get_meeting_id(self):
        hash_content = u'meeting-%s' % self.get_original_object_id()
        return unicode(sha1(hash_content.decode('utf8')).hexdigest())

    def get_combined_index_data(self):
        combined_index_data = {}

        #committees = self._get_committees()
        current_permalink = self._get_current_permalink()

        combined_index_data['id'] = unicode(self.get_object_id())

        combined_index_data['hidden'] = self.source_definition['hidden']

        combined_index_data['name'] = unicode(self._xpath("string(/activiteit/onderwerp)"))
        #combined_index_data['start_date'] = iso8601.parse_date(self._xpath("string(/activiteit/planning/begin)"))
        #print iso8601.parse_date(self._xpath("string(/activiteit/planning/einde)"))
        #combined_index_data['end_date'] = self._xpath("string(/activiteit/planning/einde)")
        combined_index_data['location'] = unicode(self._xpath("string(/activiteit/locatie)"))
        combined_index_data['classification'] = u'event_item'

        combined_index_data['children'] = [item.xpath("string(@id)") for item in self._xpath("/activiteit/agendapunt")]
        combined_index_data['attendees'] = [item.xpath("string(@id)") for item in self._xpath("/activiteit/deelnemer")]
        combined_index_data['cancelled'] = {'id': item.xpath("string(@id)") for item in self._xpath("/activiteit/afgemeld")}

        for item in self._xpath("/activiteit/kamers/*"):
            combined_index_data['organizations'] = {'id': item.xpath("string(@id)"), 'name': item.xpath("string(name())")}

        # Status might be with or without a capital
        if self._xpath("contains(/activiteit/status, 'itgevoerd')"):  # Uitgevoerd
            combined_index_data['status'] = u'completed'
        elif self._xpath("contains(/activiteit/status, 'ervplaats')"):  # Verplaatst
            combined_index_data['status'] = u'postponed'
        elif self._xpath("contains(/activiteit/status, 'epland')"):  # Gepland
            combined_index_data['status'] = u'tentative'
        elif self._xpath("contains(/activiteit/status, 'eannuleerd')"):  # Geannuleerd
            combined_index_data['status'] = u'cancelled'

        combined_index_data['identifiers'] = [
            {
                'identifier': self.get_original_object_id(),
                'scheme': u'Gegevensmagazijn'
            },
            {
                'identifier': self._xpath("string(/activiteit/vrsNummer)"),
                'scheme': u'vrsnummer'
            },
            {
                'identifier': self._xpath("string(/activiteit/nummer)"),
                'scheme': u'nummer'
            },
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            }
        ]

        # try:
        #     combined_index_data['organization'] = committees[
        #         self.original_item['dmu']['id']]
        # except KeyError:
        #     pass

        # combined_index_data['organization_id'] = unicode(
        #     self.original_item['dmu']['id'])

        combined_index_data['status'] = u'confirmed'
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


class Motion(GegevensmagazijnBaseItem, MotionItem):

    def get_object_id(self):
        return get_motion_id(self.get_original_object_id())

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['id'] = unicode(self.get_object_id())
        combined_index_data['name'] = unicode(self._xpath("string(onderwerp)"))

        combined_index_data['vote_events'] = [
            u"/%s/vote_events/%s" % (self.source_definition['index_name'],
                            get_vote_event_id(self._xpath("string(@id)")))]

        print "Motion orig:%s id:%s" % (self._xpath("string(@id)"),
                                        get_vote_event_id(self._xpath("string(@id)")))

        return combined_index_data


class VoteEvent(GegevensmagazijnBaseItem, VotingEventItem):

    def get_object_id(self):
        return get_vote_event_id(self.get_original_object_id())

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['id'] = unicode(self.get_object_id())

        combined_index_data['motion_id'] = get_motion_id(self._xpath("string("
                                                              "@id)"))
        combined_index_data['identifier'] = unicode(self._xpath("string(../volgorde)"))

        print "id:%s orig_id:%s" % (combined_index_data['id'], self._xpath("string(@id)"))
        print "motion:%s" % get_vote_event_id(self._xpath("string(@id)"))

        result = re.sub(r'[^ a-z]', '', self._xpath("string("
                                                   "slottekst)").lower())
        if result == "aangenomen":
            combined_index_data['result'] = u"pass"
        elif result == "verworpen":
            combined_index_data['result'] = u"fail"
        elif result == "aangehouden":
            combined_index_data['result'] = u"kept"
        elif result == "uitgesteld":
            combined_index_data['result'] = u"postponed"
        elif result == "ingetrokken":
            combined_index_data['result'] = u"withdrawn"
        elif result == "vervallen":
            combined_index_data['result'] = u"expired"
        elif result == "inbreng geleverd":
            combined_index_data['result'] = u"discussed"
        elif result == "vrijgegeven":
            combined_index_data['result'] = u"published"
        else:
            print "Result %s does not exists for: %s" % (result, self.original_item)

        sub_events = self.source_definition['mapping']['vote_event']['sub_items']

        combined_index_data['counts'] = [u"/%s/counts/%s" % (
            self.source_definition['index_name'], get_count_id(x)) for x in
                self._xpath(sub_events['count'] + "/@id")]
        combined_index_data['votes'] = [u"/%s/votes/%s" % (
            self.source_definition['index_name'], get_vote_id(x)) for x in
                self._xpath(sub_events['vote'] + "/@id")]

        return combined_index_data


class Count(GegevensmagazijnBaseItem, CountItem):

    def get_object_id(self):
        return get_count_id(self.get_original_object_id())

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['id'] = unicode(self.get_object_id())

        soort = unicode(self._xpath("string(soort)"))
        if soort == "Voor":
            combined_index_data['option'] = u"yes"
        elif soort == "Tegen":
            combined_index_data['option'] = u"no"
        elif soort == "Onthouding":
            combined_index_data['option'] = u"abstain"
        elif soort == "Niet deelgenomen":
            combined_index_data['option'] = u"absent"

        party = self._get_party(self._xpath("string(fractie/@ref)"))
        if party:
            party.update({"@context": OrganisationItem.ld_context, "@type":
                "http://www.w3.org/ns/org#Organization"})
            combined_index_data['group'] = party

        combined_index_data['value'] = int(self._xpath("number("
                                                       "fractieGrootte)"))

        return combined_index_data


class Vote(GegevensmagazijnBaseItem, VoteItem):

    def get_object_id(self):
        return get_vote_id(self.get_original_object_id())

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['id'] = unicode(self.get_object_id())

        soort = unicode(self._xpath("string(soort)"))
        if soort == "Voor":
            combined_index_data['option'] = u"yes"
        elif soort == "Tegen":
            combined_index_data['option'] = u"no"
        elif soort == "Onthouding":
            combined_index_data['option'] = u"abstain"
        elif soort == "Niet deelgenomen":
            combined_index_data['option'] = u"absent"

        # person = self._get_person(self._xpath("string(persoon/@ref)"))
        # if person:
        #     person.update({"@context": PersonItem.ld_context, "@type":
        #         "http://www.w3.org/ns/person#Person"})
        #     combined_index_data['group'] = person

        return combined_index_data


class Person(GegevensmagazijnBaseItem, PersonItem):

    def get_object_id(self):
        return self.get_person_id()

    def get_person_id(self):
        hash_content = u'person-%s' % self.get_original_object_id()
        return unicode(sha1(hash_content.decode('utf8')).hexdigest())

    def get_combined_index_data(self):
        combined_index_data = {}

        combined_index_data['id'] = unicode(self.get_object_id())

        combined_index_data['hidden'] = self.source_definition['hidden']

        combined_index_data['honorific_prefix'] = unicode(self._xpath("string(/persoon/titels)"))
        combined_index_data['family_name'] = unicode(self._xpath("string(/persoon/achternaam)"))
        combined_index_data['given_name'] = unicode(self._xpath("string(/persoon/voornamen)"))
        combined_index_data['name'] = u' '.join([x for x in [self._xpath("string(/persoon/roepnaam)"), self._xpath("string(/persoon/tussenvoegsel)"), combined_index_data['family_name']] if x != ''])

        gender = self._xpath("string(/persoon/geslacht)")
        if gender == 'man':
            combined_index_data['gender'] = u"male"
        elif gender == 'vrouw':
            combined_index_data['gender'] = u"female"

        if self._xpath("string(/persoon/geboortdatum)"):
            combined_index_data['birth_date'] = iso8601.parse_date(self._xpath("string(/persoon/geboortdatum)"))
        if self._xpath("string(/persoon/overlijdensdatum)"):
            combined_index_data['death_date'] = iso8601.parse_date(self._xpath("string(/persoon/overlijdensdatum)"))

        combined_index_data['national_identity'] = unicode(self._xpath("string(/persoon/geboorteland)"))
        combined_index_data['email'] = unicode(self._xpath("string(/persoon/contactinformatie[soort='E-mail']/waarde)"))
        combined_index_data['links'] = [unicode(self._xpath("string(/persoon/contactinformatie[soort='Website']/waarde)"))]

        image = self._xpath("string(/persoon/afbeelding/@ref)")
        if image:
            hashed_url = sha1(image).hexdigest()
            combined_index_data['media_urls'] = [
                {
                    "url": "/v0/resolve/%s" % hashed_url,
                    "original_url": self._get_resource_permalink(image)
                }
            ]

        combined_index_data['identifiers'] = [
            {
                'identifier': self.get_original_object_id(),
                'scheme': u'Gegevensmagazijn'
            },
            {
                'identifier': self.get_object_id(),
                'scheme': u'ORI'
            }
        ]

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


class Document(GegevensmagazijnBaseItem, PopoloBaseItem):

    def get_object_id(self):
        return get_vote_id(self.get_original_object_id())

    def get_combined_index_data(self):
        combined_index_data = {}

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
