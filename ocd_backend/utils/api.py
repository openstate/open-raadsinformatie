import json

import requests

from ocd_backend import settings


class FrontendAPIMixin(object):
    """
    Interface for the frontend API.
    """

    def api_request(self, index_name, doc_type, query=None, *args, **kwargs):

        if doc_type:
            api_url = u'%s%s/%s/search' % (
                self.source_definition.get('frontend_api_url', settings.API_URL),
                index_name, doc_type,)
        else:
            api_url = u'%s%s/search' % (
                self.source_definition.get('frontend_api_url', settings.API_URL),
                index_name,)

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
            if k in api_query:
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
        try:
            r.raise_for_status()
        except requests.HTTPError:
            return None

        if doc_type:
            try:
                return r.json()[doc_type]
            except KeyError:
                return None
        return r.json()

    def api_request_object(self, index_name, doc_type, object_id, *args,
                           **kwargs):
        api_url = u'%s%s/%s/%s' % (
            self.source_definition.get('frontend_api_url',
                                       settings.API_URL), index_name, doc_type,
            object_id)
        r = self.http_session.get(
            api_url
        )
        try:
            r.raise_for_status()
        except requests.HTTPError:
            return None

        return r.json()
