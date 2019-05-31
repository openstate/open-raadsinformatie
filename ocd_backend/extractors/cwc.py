import json
import os

from suds.client import Client  # pylint: disable=import-error
from suds.sudsobject import asdict  # pylint: disable=import-error

from ocd_backend import settings
from ocd_backend.extractors import BaseExtractor
from ocd_backend.log import get_source_logger

log = get_source_logger('extractor')


# suds serialization to json:
# https://www.snip2code.com/Snippet/15899/convert-suds-response-to-dictionary
def recursive_asdict(d):
    """Convert Suds object into serializable format."""
    out = {}
    for k, v in asdict(d).iteritems():
        if hasattr(v, '__keylist__'):
            out[k] = recursive_asdict(v)
        elif isinstance(v, list):
            out[k] = []
            for item in v:
                if hasattr(item, '__keylist__'):
                    out[k].append(recursive_asdict(item))
                else:
                    out[k].append(item)
        else:
            out[k] = v
    return out


# according to https://stackoverflow.com/questions/23285558/datetime-date2014-4-25-is-not-json-serializable-in-django
def date_handler(obj):
    return obj.isoformat() if hasattr(obj, 'isoformat') else obj


def suds_to_json(data):
    return json.dumps(recursive_asdict(data), default=date_handler)


class CompanyWebcastBaseExtractor(BaseExtractor):
    """
    A base extractor for the CWC SOAP service. Instantiates the client
    and configures the right port to use.
    """

    def run(self):
        pass

    def __init__(self, *args, **kwargs):
        super(CompanyWebcastBaseExtractor, self).__init__(*args, **kwargs)

        self.client = Client(settings.CWC_WSDL)
        self.username = os.environ.get('%s.cwc_username' % self.source_definition['key'])
        self.password = os.environ.get('%s.cwc_password' % self.source_definition['key'])
        # self.client.set_options(port='BasicHttpsBinding_IPublic')


class VideotulenExtractor(CompanyWebcastBaseExtractor):
    """
    Extracts Videotulen from the CWC SOAP API
    """

    def run(self):
        current_page = 0
        consecutive_errors = 0
        result_count = 0
        pagesize = self.source_definition.get('cwc_pagesize', 10)

        while consecutive_errors < 5:
            log.debug("[%s] Requesting cwc page %s ..." % (self.source_definition['key'], current_page,))
            results = self.client.service.WebcastSearch(
                Username=self.username,
                Password=self.password,
                PageSize=pagesize,
                PageNumber=current_page,
                Order='CreatedDesc'
            )

            if results.WebcastSearchResult == 3:
                log.warning("[%s] CompanyWebcast credentials are incorrect" % self.source_definition['key'])
                break

            elif results.WebcastSearchResult != 0:
                log.warning("[%s] CompanyWebcast page %s resulted in error code : %s" % (
                    self.source_definition['key'], current_page, results.WebcastSearchResult)
                )

                consecutive_errors += 1
                current_page += 1
                continue

            if len(results.WebcastSummaries) < 1:
                break

            for result in results.WebcastSummaries[0]:
                full_result = self.client.service.WebcastGet(
                    Username=self.username,
                    Password=self.password,
                    Code=result.Code)

                result_count += 1
                if full_result.WebcastGetResult != 0:
                    log.warning("[%s] Webcast %s resulted in error code : %s" % (
                        self.source_definition['key'], result.Code, full_result.WebcastGetResult,))
                    consecutive_errors += 1
                    continue

                # if full_result is not None and full_result['Webcast'] is not None:
                #     log.debug("%s: %s" % (
                #         full_result['Webcast']['Title'],
                #         full_result['Webcast']['ScheduledStart'],))

                serialized_result = suds_to_json(full_result)
                yield 'application/json', serialized_result
                consecutive_errors = 0

            current_page += 1

        log.info("[%s] Extracted total of %d cwc results" % (self.source_definition['index_name'], result_count))
