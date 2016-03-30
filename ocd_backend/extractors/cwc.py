import json
from pprint import pprint
import re

from lxml import etree
from suds.client import Client
from suds.sudsobject import asdict

from ocd_backend.extractors import BaseExtractor, HttpRequestMixin
from ocd_backend.exceptions import ConfigurationError

from ocd_backend import settings
from ocd_backend.utils.ibabs import (
    meeting_to_dict, document_to_dict, meeting_item_to_dict,
    meeting_type_to_dict, list_report_response_to_dict,
    list_entry_response_to_dict)


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

    def __init__(self, *args, **kwargs):
        super(CompanyWebcastBaseExtractor, self).__init__(*args, **kwargs)

        self.client = Client(settings.CWC_WSDL)
        # self.client.set_options(port='BasicHttpsBinding_IPublic')


class VideotulenExtractor(CompanyWebcastBaseExtractor):
    """
    Extracts Videotulen from the CWC SOAP API
    """

    def run(self):
        current_page = 0
        pagesize = self.source_definition['cwc_pagesize']
        result_count = pagesize

        while (result_count == pagesize):
            results = self.client.service.WebcastSearch(
                Username=self.source_definition['cwc_username'],
                Password=self.source_definition['cwc_password'],
                PageSize=self.source_definition['cwc_pagesize'],
                PageNumber=current_page)

            result_count = 0
            for result in results.WebcastSummaries[0]:
                full_result = self.client.service.WebcastGet(
                    Username=self.source_definition['cwc_username'],
                    Password=self.source_definition['cwc_password'],
                    Code=result.Code)
                serialized_result = suds_to_json(full_result)
                yield 'application/json', serialized_result
                result_count += 1
            if not self.source_defitinion['cwc_paging']:
                result_count = 0
            current_page += 1
