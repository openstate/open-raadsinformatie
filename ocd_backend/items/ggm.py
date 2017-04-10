from hashlib import sha1
import iso8601

from ocd_backend.items.popolo import EventItem, MotionItem, PersonItem


class GegevensmagazijnBaseItem(object):

    def _xpath(self, path):
        return self.original_item.xpath(path)

    def _get_current_permalink(self):
        return u'https://gegevensmagazijn.tweedekamer.nl/REST/Entiteiten/%s' % self.get_object_id()

    def get_object_id(self):
        raise NotImplementedError

    def get_original_object_id(self):
        return unicode(self._xpath("string(/*/@id)"))

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
        return self.get_motion_id()

    def get_motion_id(self):
        hash_content = u'motion-%s' % self.get_original_object_id()
        return unicode(sha1(hash_content.decode('utf8')).hexdigest())

    def get_combined_index_data(self):
        combined_index_data = {}
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

        combined_index_data['identifiers'] = [
            {
                'identifier': self.get_original_object_id(),
                'scheme': u'Gegevensmagazijn'
            },
            {
                'identifier': unicode(self.get_object_id()),
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
