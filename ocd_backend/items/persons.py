from urlparse import urljoin

from lxml import etree

from ocd_backend.items import BaseItem
from ocd_backend.models import *
from ocd_backend.models.model import Relationship
from ocd_backend.utils.http import HttpRequestMixin
from ocd_backend.log import get_source_logger

log = get_source_logger('persons')


class AlmanakPersonItem(BaseItem):
    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        source_defaults = {
            'source': 'almanak',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        person = Person(self.original_item['id'], **source_defaults)
        person.name = self.original_item['name']
        person.email = self.original_item['email']
        person.gender = self.original_item['gender']

        municipality = Organization(self.source_definition['almanak_id'], **source_defaults)
        municipality.name = self.source_definition['sitename']

        municipality_member = Membership(**source_defaults)
        municipality_member.organization = municipality
        # TODO: Setting member = person causes infinite recursion
        # municipality_member.member = person
        municipality_member.role = self.original_item['role']

        person.member_of = [municipality_member]

        if self.original_item['party']:
            party = Organization(self.original_item['party'], **source_defaults)
            party.name = self.original_item['party']

            party_member = Membership(**source_defaults)
            party_member.organization = party
            # TODO: Setting member = person causes infinite recursion
            # party_member.member = person
            party_member.role = self.original_item['role']

            person.member_of.append(party_member)

        return person


class HTMLPersonItem(HttpRequestMixin, BaseItem):
    def _get_name(self):
        return u''.join(
            self.original_item.xpath(
                self.source_definition.get(
                    'persons_name_xpath', './/h2//text()'))).strip()

    def get_rights(self):
        return u'undefined'

    def get_collection(self):
        return unicode(self.source_definition['index_name'])

    def get_object_model(self):
        source_defaults = {
            'source': 'almanak',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        pname = self._get_name()
        person = Person(pname, **source_defaults)
        person.name = self._get_name()

        return person


class HTMLPersonFromLinkItem(HTMLPersonItem):
    def get_object_model(self):
        person = super(HTMLPersonFromLinkItem, self).get_object_model()

        source_defaults = {
            'source': 'almanak',
            'source_id_key': 'identifier',
            'organization': self.source_definition['key'],
        }

        # log.info(etree.tostring(self.original_item))
        # log.info('Persons URL path: %s' % (self.source_definition['persons_link_path'],))
        try:
            request_url = urljoin(
                self.source_definition['file_url'],
                self.original_item.xpath(
                    self.source_definition['persons_link_path'])[0])
        except LookupError as e:
            log.error(e)
            return person

        log.info('Now downloading URL: %s' % (request_url,))
        r = self.http_session.get(request_url, verify=False)
        r.raise_for_status()
        html = etree.HTML(r.content)

        try:
            person.email = html.xpath(
                'string(//a[starts-with(@href,"mailto:")]/text())').strip().split(' ')[0]
        except LookupError:
            pass

        # TODO: not sure how to determine gender
        # person.gender = u'male' if person.name.startswith(u'Dhr. ') else u'female'

        municipality = Organization(
            self.source_definition['almanak_id'], **source_defaults)
        if municipality is None:
            log.debug('Could not find almanak organization')
            return person

        party_name = u''.join(html.xpath(
            self.source_definition['organization_xpath']))
        party = Organization(party_name, **source_defaults)

        municipality_member = Membership()
        municipality_member.organization = municipality
        # TODO: Setting member = person causes infinite recursion
        # municipality_member.member = person
        municipality_member.role = 'Fractielid'
        # municipality_member.role = html.xpath('string(//div[@id="content"]//h3/text())').strip()
        party_member = Membership()
        party_member.organization = party
        # TODO: Setting member = person causes infinite recursion
        # party_member.member = person
        party_member.role = 'Member'

        person.member_of = [municipality_member, party_member]

        # person.member_of(municipality_member, party_member, rel=party)

        # person.member_of = Relationship(municipality, rel=party)

        return person
