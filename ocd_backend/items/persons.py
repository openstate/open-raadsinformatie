from urlparse import urljoin

from lxml import etree

from ocd_backend.items import BaseItem
from ocd_backend.models import *
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
        person.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        person.has_organization_name.merge(collection=self.source_definition['key'])

        person.name = self.original_item['name']
        person.email = self.original_item['email']
        person.gender = self.original_item['gender']

        municipality = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        municipality.merge(collection=self.source_definition['key'])

        municipality_member = Membership(**source_defaults)
        municipality_member.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        municipality_member.has_organization_name.merge(collection=self.source_definition['key'])

        municipality_member.organization = municipality
        municipality_member.member = person
        municipality_member.role = self.original_item['role']

        person.member_of = [municipality_member]

        if self.original_item['party']:
            party = Organization(self.original_item['party'], **source_defaults)
            party.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
            party.has_organization_name.merge(collection=self.source_definition['key'])

            party.name = self.original_item['party']
            party_member = Membership(**source_defaults)
            party_member.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
            party_member.has_organization_name.merge(collection=self.source_definition['key'])

            party_member.organization = party
            party_member.member = person
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
        person.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        person.has_organization_name.merge(collection=self.source_definition['key'])
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

        municipality = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        municipality.merge(collection=self.source_definition['key'])

        party_name = u''.join(html.xpath(self.source_definition['organization_xpath']))
        party = Organization(party_name, **source_defaults)
        party.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        party.has_organization_name.merge(collection=self.source_definition['key'])

        municipality_member = Membership()
        municipality_member.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        municipality_member.has_organization_name.merge(collection=self.source_definition['key'])

        municipality_member.organization = municipality
        municipality_member.member = person
        municipality_member.role = 'Fractielid'

        party_member = Membership()
        party_member.has_organization_name = TopLevelOrganization(self.source_definition['key'], **source_defaults)
        party_member.has_organization_name.merge(collection=self.source_definition['key'])

        party_member.organization = party
        party_member.member = person
        party_member.role = 'Member'

        person.member_of = [municipality_member, party_member]

        return person
