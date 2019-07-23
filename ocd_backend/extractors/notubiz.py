import json

from requests.exceptions import HTTPError, RetryError

from ocd_backend.exceptions import ItemAlreadyProcessed
from ocd_backend.extractors import BaseExtractor
from ocd_backend.log import get_source_logger
from ocd_backend.utils.http import GCSCachingMixin

log = get_source_logger('extractor')


class NotubizBaseExtractor(BaseExtractor, GCSCachingMixin):
    """
    A base extractor for the Notubiz API. This base extractor configures the base url
    to use for accessing the API and creates an 'organizations' dictionary that contains
    information needed by child classes.
    """

    def run(self):
        raise NotImplementedError

    def __init__(self, *args, **kwargs):
        super(NotubizBaseExtractor, self).__init__(*args, **kwargs)

        self.base_url = self.source_definition['base_url']
        # Set the bucket name for Google Cloud Storage
        self.bucket_name = 'notubiz'

        response = self.http_session.get(
            "%s/organisations"
            "?format=json&version=1.10.8" % self.base_url
        )

        try:
            response.raise_for_status()
        except HTTPError, e:
            log.warning('[%s] %s: %s' % (self.source_definition['sitename'], e, response.request.url))
            return

        # Create a dictionary of Notubiz organizations. Some child classes need information
        # from this dictionary.
        self.organizations = dict()
        for organization in response.json()['organisations']['organisation']:
            attributes = dict()
            for field in organization['settings']['folder']['fields']['field']:
                attributes[field['@attributes']['id']] = field['label']
            self.organizations[organization['@attributes']['id']] = {
                'logo': organization['logo'],
                'attributes': attributes,
            }


class NotubizCommitteesExtractor(NotubizBaseExtractor):
    """
    Extracts committees ('gremia') from Notubiz.
    """

    def run(self):
        response = self.http_session.get(
            "%s/organisations/%s/gremia"
            "?format=json&version=1.10.8" % (self.base_url, self.source_definition['notubiz_organization_id'])
        )
        response.raise_for_status()

        committee_count = 0
        for committee in json.loads(response.content)['gremia']:
            entity = '%s/organisations/%s/gremia/%s?format=json&version=1.10.8' % (
                self.base_url,
                self.source_definition['notubiz_organization_id'],
                committee['id'])
            yield 'application/json', \
                  json.dumps(committee), \
                  entity, \
                  committee
            committee_count += 1

        log.info("[%s] Extracted total of %d notubiz committees." % (self.source_definition['sitename'], committee_count))


class NotubizMeetingsExtractor(NotubizBaseExtractor):
    """
    Extracts meetings from Notubiz.
    """

    def run(self):
        meeting_count = 0
        meetings_skipped = 0

        start_date, end_date = self.date_interval()

        log.debug("Now processing first page meeting(items) from %s to %s" % (
            start_date, end_date,))

        page = 1
        while True:
            try:
                response = self.http_session.get(
                    "%s/events?organisation_id=%i&date_from=%s&date_to=%s"
                    "&format=json&version=1.10.8&page=%i" %
                    (
                        self.base_url,
                        self.source_definition['notubiz_organization_id'],
                        start_date.strftime("%Y-%m-%d %H:%M:%S"),
                        end_date.strftime("%Y-%m-%d %H:%M:%S"),
                        page
                    )
                )
            except (HTTPError, RetryError), e:
                log.warning('[%s] %s: %s' % (self.source_definition['sitename'], e, response.request.url))
                break

            try:
                response.raise_for_status()
            except HTTPError, e:
                log.warning('[%s] %s: %s' % (self.source_definition['sitename'], e, response.request.url))
                break

            event_json = response.json()

            if not event_json[self.source_definition['doc_type']]:
                break

            if page > 1:
                log.debug("[%s] Processing events page %i" % (self.source_definition['sitename'], page))

            for item in event_json[self.source_definition['doc_type']]:
                try:
                    data = self.fetch_data(
                        "%s/events/meetings/%i?format=json&version=1.10.8" %
                        (
                            self.base_url,
                            item['id']
                        ),
                        "events/meetings/%i" % item['id'],
                        item['last_modified'],
                    )
                    meeting_json = json.loads(data)['meeting']
                except ItemAlreadyProcessed, e:
                    # This should no longer be triggered after the change to GCS caching
                    meetings_skipped += 1
                    log.debug("[%s] %s" % (self.source_definition['sitename'], e))
                    continue
                except Exception as e:
                    meetings_skipped += 1
                    log.warning('[%s] %s: %s' % (self.source_definition['sitename'], e, response.request.url))
                    continue

                organization = self.organizations[self.source_definition['notubiz_organization_id']]

                attributes = {}
                for meeting in meeting_json['attributes']:
                    try:
                        attributes[organization['attributes'][meeting['id']]] = meeting['value']
                    except KeyError:
                        pass
                meeting_json['attributes'] = attributes

                entity = "%s/events?organisation_id=%i&date_from=%s&date_to=%s&format=json&version=1.10.8&page=%i" % (
                        self.base_url,
                        self.source_definition['notubiz_organization_id'],
                        start_date.strftime("%Y-%m-%d %H:%M:%S"),
                        end_date.strftime("%Y-%m-%d %H:%M:%S"),
                        page
                    )

                yield 'application/json', \
                      json.dumps(meeting_json), \
                      entity, \
                      meeting_json
                meeting_count += 1

            page += 1

            if not event_json['pagination']['has_more_pages']:
                log.debug("[%s] Done processing all %d pages!" % (self.source_definition['sitename'], page))
                break

        log.info("[%s] Extracted total of %d notubiz meeting(items). Also skipped %d "
                 "meetings in total." % (self.source_definition['sitename'], meeting_count, meetings_skipped,))


# class NotubizMeetingItemExtractor(NotubizBaseExtractor):
#     def extractor(self, meeting_json):
#         for meeting_item in meeting_json.get('agenda_items', []):
#             attributes = {}
#             for item in meeting_item['type_data'].get('attributes', []):
#                 try:
#                     attributes[self.organization['attributes'][item['id']]] = item['value']
#                 except KeyError:
#                     pass
#             meeting_item['attributes'] = attributes
#             yield 'application/json', json.dumps(meeting_item)
#
#             # Recursion for subitems if any
#             for result in self.extractor(meeting_item):
#                 # Re-yield all results
#                 yield result
