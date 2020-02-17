import json
from urllib import parse

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
    base_url = 'https://api.notubiz.nl'
    application_token = '&application_token=11ef5846eaf0242ec4e0bea441379d699a77f703d'
    default_query_params = 'format=json&version=1.17.0'

    def run(self):
        raise NotImplementedError

    def __init__(self, *args, **kwargs):
        super(NotubizBaseExtractor, self).__init__(*args, **kwargs)

        # Set the bucket name for Google Cloud Storage
        self.bucket_name = 'notubiz'

        response = self.http_session.get(
            "%s/organisations?%s" % (self.base_url, self.default_query_params)
        )

        try:
            response.raise_for_status()
        except HTTPError as e:
            log.warning(f'[{self.source_definition["key"]}] {str(e)}: {response.request.url}')
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
        committee_url = "%s/organisations/%s/gremia?%s" % (
            self.base_url,
            self.source_definition['notubiz_organization_id'],
            self.default_query_params
        )
        cached_path = 'gremia'
        response = self.fetch(committee_url + self.application_token, cached_path, None)

        committee_count = 0
        for committee in json.load(response.media_file)['gremia']:

            yield 'application/json', \
                  json.dumps(committee), \
                  committee_url, \
                  'notubiz/' + cached_path,
            committee_count += 1

        log.info(f'[{self.source_definition["key"]}] Extracted total of {committee_count} notubiz committees.')


class NotubizMeetingsExtractor(NotubizBaseExtractor):
    """
    Extracts meetings from Notubiz.
    """

    def run(self):
        meeting_count = 0
        meetings_skipped = 0

        start_date, end_date = self.date_interval()

        log.debug(f'[{self.source_definition["key"]}] Now processing first page meeting(items) from {start_date} to {end_date}')

        page = 1
        while True:
            url = "%s/events?organisation_id=%i&date_from=%s&date_to=%s&page=%i&%s" % (
                        self.base_url,
                        self.source_definition['notubiz_organization_id'],
                        start_date.strftime("%Y-%m-%d %H:%M:%S"),
                        end_date.strftime("%Y-%m-%d %H:%M:%S"),
                        page,
                        self.default_query_params,
                    )
            try:
                response = self.http_session.get(url)
            except (HTTPError, RetryError) as e:
                log.warning(f'[{self.source_definition["key"]}] {str(e)}: {parse.quote(url)}')
                break

            try:
                response.raise_for_status()
            except HTTPError as e:
                log.warning(f'[{self.source_definition["key"]}] {str(e)}: {response.request.url}')
                break

            event_json = response.json()

            if not event_json[self.source_definition['doc_type']]:
                break

            if page > 1:
                log.debug(f'[{self.source_definition["key"]}] Processing events page {page}')

            for item in event_json[self.source_definition['doc_type']]:
                # Skip meetings that are not public
                if item['permission_group'] != 'public':
                    meetings_skipped += 1
                    continue

                meeting_url = "%s/events/meetings/%i?%s" % (
                    self.base_url,
                    item['id'],
                    self.default_query_params
                )
                cached_path = "events/meetings/%i" % item['id']
                try:
                    resource = self.fetch(meeting_url + self.application_token, cached_path, item['last_modified'])
                    meeting_json = json.load(resource.media_file)['meeting']
                except ItemAlreadyProcessed as e:
                    # This should no longer be triggered after the change to GCS caching
                    meetings_skipped += 1
                    log.debug(f'[{self.source_definition["key"]}] {str(e)}')
                    continue
                except HTTPError as e:
                    error_json = e.response.json()
                    if error_json.get('message') == 'No rights to see this meeting':
                        log.info(f'[{self.source_definition["key"]}] No rights to view: {meeting_url}')
                        break
                    # Reraise all other HTTP errors
                    raise
                except Exception as e:
                    meetings_skipped += 1
                    log.warning(f'[{self.source_definition["key"]}] {str(e)}: {meeting_url}')
                    continue

                organization = self.organizations[self.source_definition['notubiz_organization_id']]

                attributes = {}
                for meeting in meeting_json['attributes']:
                    try:
                        attributes[organization['attributes'][meeting['id']]] = meeting['value']
                    except KeyError:
                        pass
                meeting_json['attributes'] = attributes

                yield 'application/json', \
                      json.dumps(meeting_json), \
                      meeting_url, \
                      'notubiz/' + cached_path,
                meeting_count += 1

            page += 1

            if not event_json['pagination']['has_more_pages']:
                log.debug(f'[{self.source_definition["key"]}] Done processing all {page} pages')
                break

        log.info(f'[{self.source_definition["key"]}] Extracted total of {meeting_count} notubiz meeting(items). '
                 f'Also skipped {meetings_skipped} meetings')


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
