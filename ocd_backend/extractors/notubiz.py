import json

from requests.exceptions import HTTPError, RetryError
from urllib3.exceptions import MaxRetryError

from ocd_backend.extractors import BaseExtractor, HTTPCachingMixin
from ocd_backend.log import get_source_logger

log = get_source_logger('extractor')


class NotubizBaseExtractor(BaseExtractor, HTTPCachingMixin):
    """
    A base extractor for the Notubiz API. This base extractor just
    configures the base url to use for accessing the API.
    """

    def __init__(self, *args, **kwargs):
        super(NotubizBaseExtractor, self).__init__(*args, **kwargs)
        self.base_url = self.source_definition['base_url']

    def extractor(self, meeting_json):
        raise NotImplementedError

    def run(self):
        resp = self.http_session.get(
            "%s/organisations"
            "?format=json&version=1.10.8" % self.base_url
        )

        try:
            resp.raise_for_status()
        except HTTPError, e:
            log.warning('%s: %s' % (e, resp.request.url))
            return

        organizations = dict()
        for organization in resp.json()['organisations']['organisation']:

            attributes = dict()
            for field in organization['settings']['folder']['fields']['field']:
                attributes[field['@attributes']['id']] = field['label']

            organizations[organization['@attributes']['id']] = {
                'logo': organization['logo'],
                'attributes': attributes,
            }

        meeting_count = 0
        meetings_skipped = 0

        start_date, end_date = self.date_interval()

        log.info("Now processing first page meeting(items) from %s to %s" % (
            start_date, end_date,))

        page = 1
        while True:
            try:
                resp = self.http_session.get(
                    "%s/events?organisation_id=%i&date_from=%s&date_to=%s"
                    "&format=json&version=1.10.8&page=%i" %
                    (
                        self.base_url,
                        self.source_definition['organisation_id'],
                        start_date.strftime("%Y-%m-%d %H:%M:%S"),
                        end_date.strftime("%Y-%m-%d %H:%M:%S"),
                        page
                    )
                )
            except (HTTPError, RetryError), e:
                log.warning('%s: %s' % (e, resp.request.url))
                break

            try:
                resp.raise_for_status()
            except HTTPError, e:
                log.warning('%s: %s' % (e, resp.request.url))
                break

            event_json = resp.json()

            if not event_json[self.source_definition['doc_type']]:
                break

            if page > 1:
                log.debug("Processing page %i" % page)

            for item in event_json[self.source_definition['doc_type']]:
                try:
                    data = self.fetch(
                        "%s/events/meetings/%i?format=json&version=1.10.8" %
                        (
                            self.base_url,
                            item['id']
                        ),
                        item['last_modified'],
                    )

                    meeting_json = json.loads(data)['meeting']
                except (HTTPError, RetryError), e:
                    meetings_skipped += 1
                    log.warning('%s: %s' % (e, resp.request.url))
                    continue
                except (ValueError, KeyError), e:
                    meetings_skipped += 1
                    log.error('%s: %s' % (e, resp.request.url))
                    continue

                self.organization = organizations[self.source_definition['organisation_id']]

                for result in self.extractor(meeting_json):
                    meeting_count += 1
                    yield result

            page += 1

            if not event_json['pagination']['has_more_pages']:
                log.info("Done processing all pages!")
                break

        log.info("Extracted total of %d meeting(items). Also skipped %d "
                 "meetings in total." % (meeting_count, meetings_skipped,))


class NotubizMeetingExtractor(NotubizBaseExtractor):
    def extractor(self, meeting_json):
        attributes = {}
        for item in meeting_json['attributes']:
            try:
                attributes[self.organization['attributes'][item['id']]] = item['value']
            except KeyError:
                pass
        meeting_json['attributes'] = attributes
        yield 'application/json', json.dumps(meeting_json)


class NotubizMeetingItemExtractor(NotubizBaseExtractor):
    def extractor(self, meeting_json):
        for meeting_item in meeting_json.get('agenda_items', []):
            attributes = {}
            for item in meeting_item['type_data'].get('attributes', []):
                try:
                    attributes[self.organization['attributes'][item['id']]] = item['value']
                except KeyError:
                    pass
            meeting_item['attributes'] = attributes
            yield 'application/json', json.dumps(meeting_item)

            # Recursion for subitems if any
            for result in self.extractor(meeting_item):
                # Re-yield all results
                yield result
