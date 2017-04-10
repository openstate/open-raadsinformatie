import os
import json
from base64 import b64encode

from ocd_backend import celery_app
from ocd_backend.extractors import BaseExtractor, HttpRequestMixin


class GegevensmagazijnBaseExtractor(BaseExtractor, HttpRequestMixin):

    def __init__(self, **kwargs):
        super(GegevensmagazijnBaseExtractor, self).__init__(source_definition=kwargs['source_definition'])
        self.http_session.headers['Authorization'] = 'Basic %s' % b64encode('%s:%s' % (self.source_definition['ggm_username'], self.source_definition['ggm_password']))
        self.base_url = self.source_definition['base_url']


class GegevensmagazijnEntityExtractor(HttpRequestMixin, celery_app.Task):

    def run(self, item, **kwargs):
        self.source_definition = kwargs['source_definition']
        self.http_session.headers['Authorization'] = 'Basic %s' % b64encode('%s:%s' % (self.source_definition['ggm_username'], self.source_definition['ggm_password']))
        self.http_session.headers['Accept'] = 'application/xml; charset="utf-8"'
        resp = self.http_session.get(item)
        return 'application/xml', resp.content


class GegevensmagazijnFeedExtractor(GegevensmagazijnBaseExtractor):

    def run(self, piket=None, **kwargs):
        while True:
            if piket:
                print "Downloading:", piket
                resp = self.http_session.get(u'%s&piket=%s' % (self.base_url, piket))
            elif os.environ.get('GGM_PIKET'):
                print "Downloading using env:", os.environ.get('GGM_PIKET')
                resp = self.http_session.get(
                    u'%s&piket=%s' % (self.base_url, os.environ['GGM_PIKET']))
            else:
                print "Downloading the base_url"
                resp = self.http_session.get(self.base_url)

            if resp.status_code == 200:
                feed = json.loads(resp.content)

                for entry in feed['entries']:
                    yield (entry['content']['src'],)

                try:
                    next_piket = [link["href"] for link in feed['links'] if link['rel'] == 'next'][0]
                    os.environ['GGM_PIKET'] = next_piket.split('=')[-1]
                    os.putenv('GGM_PIKET', next_piket.split('=')[-1])
                except:
                    if 'resume' in [link['rel'] for link in feed['links']]:
                        print "DONE!!!"
                        break
                    else:
                        raise Exception("No next piket or resume found")
            else:
                print resp.status_code
                #raise  # todo fix this!
                break
