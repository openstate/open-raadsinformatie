from ocd_backend.es import elasticsearch as es


class FrontendAPIMixin(object):
    """
    Deprecated. Legacy interface for emulating the old frontend API.
    """

    def api_request(self, index_name, doc_type, query=None, *args, **kwargs):
        api_query = {
            "filters": {},
            "from": 0,
            "size": 10,
            "sort": "_score",
            "order": "asc"
        }

        kwargs['@type'] = doc_type

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

        return es.search(index=index_name, body=api_query)
