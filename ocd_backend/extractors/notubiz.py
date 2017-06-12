import json

from ocd_backend.extractors import BaseExtractor, HttpRequestMixin


class NotubizBaseExtractor(BaseExtractor, HttpRequestMixin):
    """
    A base extractor for the Notubiz API. This base extractor just
    configures the base url to use for accessing the API.
    """

    def __init__(self, *args, **kwargs):
        super(NotubizBaseExtractor, self).__init__(*args, **kwargs)

        self.base_url = self.source_definition['base_url']

    def run(self):
        page = 1

        while True:
            resp = self.http_session.get("%s?format=json&page=%i" % (self.base_url, page))

            page += 1
            if page % 10 == 0:
                print "Processed %i" % page

            if resp.status_code == 200:
                static_json = json.loads(resp.content)

                for item in static_json['results']:
                    yield 'application/json', json.dumps(item)

                if static_json['next'] == None:
                    print "Done!"
                    break
            else:
                print "Error! Not a 200!"
                break
