import json

from requests import HTTPError
from dateutil.parser import parse
from ocd_backend.extractors import BaseExtractor, HttpRequestMixin
from ocd_backend.log import get_source_logger

log = get_source_logger('extractor')


class NotubizBaseExtractor(BaseExtractor, HttpRequestMixin):
    """
    A base extractor for the Notubiz API. This base extractor just
    configures the base url to use for accessing the API.
    """

    def __init__(self, *args, **kwargs):
        super(NotubizBaseExtractor, self).__init__(*args, **kwargs)
        self.base_url = self.source_definition['base_url']

    def extractor(self, meeting_json):
        raise NotImplemented

    def run(self):
        for start_date, end_date in self.interval_generator():
            log.info("Now processing first page meeting(items) from %s to %s" % (
            start_date, end_date,))

            page = 1
            while True:
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

                try:
                    resp.raise_for_status()
                except HTTPError, e:
                    log.warn('%s: %s' % (e, resp.request.url))
                    break

                event_json = resp.json()

                if not event_json[self.source_definition['doc_type']]:
                    break

                if page > 1:
                    log.debug("Processing page %i" % page)

                for item in event_json[self.source_definition['doc_type']]:
                    resp = self.http_session.get(
                        "%s/events/meetings/%i?format=json&version=1.10.8" %
                        (
                            self.base_url,
                            item['id']
                        )
                    )

                    try:
                        resp.raise_for_status()
                        meeting_json = resp.json()['meeting']
                    except HTTPError, e:
                        log.warn('%s: %s' % (e, resp.request.url))
                        break
                    except (ValueError, KeyError), e:
                        log.error('%s: %s' % (e, resp.request.url))
                        break

                    for result in self.extractor(meeting_json):
                        yield result

                # Currently not working due to bug
                # if not event_json['pagination']['has_more_pages']:
                #     log.info("Done processing all entities!")
                #     break

                page += 1


class NotubizMeetingExtractor(NotubizBaseExtractor):
    def extractor(self, meeting_json):
        meeting_json['attributes'] = {
            item['id']: item['value']
            for item in meeting_json['attributes']
        }
        yield 'application/json', json.dumps(meeting_json)


class NotubizMeetingItemExtractor(NotubizBaseExtractor):
    def extractor(self, meeting_json):
        for meeting_item in meeting_json.get('agenda_items', []):
            meeting_item['attributes'] = {
                item['id']: item['value']
                for item in meeting_item['type_data'].get('attributes', [])
            }
            yield 'application/json', json.dumps(meeting_item)

            # Recursion for subitems if any
            for result in self.extractor(meeting_item):
                # Re-yield all results
                yield result
