from datetime import datetime
import json
from pprint import pprint

import iso8601

from ocd_backend import settings


class FrontendAPIMixin(object):
    """
    Interface for the frontend API.
    """

    def api_request(self, index_name, doc_type, query=None, *args, **kwargs):
        api_url = u'%s%s/%s/search' % (
            self.source_definition.get('frontend_api_url', settings.API_URL),
            index_name, doc_type,)

        # TODO: facets (better), sorting
        api_query = {
            "facets": {},
            "filters": {},
            "from": 0,
            "size": 10,
            "sort": "_score",
            "order": "asc"
        }

        if query is not None:
            api_query["query"] = query

        for k, v in kwargs.iteritems():
            if api_query.has_key(k):
                api_query[k] = v
            else:
                if isinstance(v, basestring):
                    api_query["filters"][k] = {"terms": [v]}
                elif isinstance(v, list):
                    api_query["filters"][k] = {"terms": v}
                else:
                    api_query["filters"][k] = v

        r = self.http_session.post(
            api_url,
            data=json.dumps(api_query)
        )
        r.raise_for_status()
        try:
            return r.json()[doc_type]
        except KeyError, e:
            return None
