import json
import os
import time
from base64 import b64encode
from hashlib import sha1
from urllib import urlencode
from urlparse import urlparse, urlunparse, parse_qs

import dateutil.parser
import redis

from ocd_backend.extractors import BaseExtractor, HttpRequestMixin
from ocd_backend.log import get_source_logger
from ocd_backend.settings import REDIS_HOST, REDIS_PORT, DATA_DIR_PATH
from ocd_backend.utils.misc import get_secret

log = get_source_logger('loader')


class GegevensmagazijnBaseExtractor(BaseExtractor, HttpRequestMixin):
    def run(self):
        pass

    def __init__(self, source_definition):
        super(GegevensmagazijnBaseExtractor, self).__init__(source_definition=source_definition)
        user, password = get_secret(self.source_definition['id'])
        self.http_session.headers['Authorization'] = 'Basic %s' % b64encode('%s:%s' % (user, password))
        self.feed_url = self.source_definition['base_url'] + self.source_definition['feed_query']
        self.redis = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=1)


class GegevensmagazijnFeedExtractor(GegevensmagazijnBaseExtractor):
    def run(self):
        self.url_hash = sha1(self.feed_url.encode("UTF-8")).hexdigest()[:6]
        self.path = os.path.join(DATA_DIR_PATH, self.source_definition['xml_directory'])
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        second_last_piket, last_piket = self.get_last_pikets()

        if self.source_definition.get('resume_last'):
            log.info("Configuration 'resume_last' set, resuming second last url:\n%s" %
                     self.piket_to_url(second_last_piket))
        else:
            pikets = self.get_pikets()
            if second_last_piket:
                log.info(
                    "Yielding all entities for %i pikets from redis cache for url:\n%s" % (len(pikets), self.feed_url))

            i = 0
            for piket in pikets:
                for entity_id, modified_seconds in self.get_piket_entities(piket).items():
                    data = self.fetch_entity(piket, entity_id, modified_seconds)
                    i += 1
                    yield 'application/xml', data

            if i:
                log.info("There were %i cached entity id's yielded" % i)

        # Starting at the second last piket if available to check if the last
        # piket is still the same
        piket = second_last_piket

        while True:
            if piket:
                log.debug("Downloading next piket: %s" % piket)
            else:
                self.redis.set('%s_url' % self.url_hash, self.feed_url)
                log.debug("Downloading 'base_url' in configuration, "
                          "since redis cache for this url is empty")

            self.http_session.headers['Accept'] = 'application/json; charset="utf-8"'
            resp = self.http_session.get(self.piket_to_url(piket))
            resp.raise_for_status()

            feed = json.loads(resp.content)

            for entry in feed['entries']:
                item = entry['content']['src']
                entity_id = item.rsplit('/', 1)[1]

                updated = entry.get('updated')
                if updated:
                    dt = dateutil.parser.parse(updated)
                    modified_seconds = int(time.mktime(dt.timetuple()))
                    data = self.fetch_entity(piket, entity_id, modified_seconds)
                    self.push_entity(piket, entity_id, modified_seconds)
                    if data:
                        yield 'application/xml', data
                else:
                    log.warning("The GGM feed featured an entry that had no "
                             "'updated' field. Exiting. %s" % entry)
                    break

            try:
                next_url = [link["href"] for link in feed['links'] if link['rel'] == 'next'][0]
            except IndexError:
                if 'resume' in [link['rel'] for link in feed['links']]:
                    log.info("Done processing! 'resume' was found.")
                    break
                else:
                    log.fatal("Neither the next piket or 'resume' was found. "
                              "Exiting.")
                    break

            next_piket = self.url_to_piket(next_url)

            # Check if the next piket is the same as the last one in redis
            if last_piket and next_piket != last_piket:
                log.fatal('The next piket doesn\'t match the last piket that '
                          'was cached in redis! Maybe the data has changed. '
                          'All keys in redis starting with %s need to be '
                          'deleted to continue. Exiting.' % self.url_hash)
                break

            if not last_piket:
                self.push_piket(next_piket)

            # Passed the check so disabling it for next iteration
            last_piket = None

            if piket == next_piket:
                log.fatal('The next piket is the same as the current one! '
                          'Exiting.')
                break

            piket = next_piket

    def download_entity(self, file_path, entity_id):
        self.http_session.headers[
            'Accept'] = 'application/xml; charset="utf-8"'
        resp = self.http_session.get(
            '%sEntiteiten/%s' % (
                self.source_definition['base_url'],
                entity_id
            ),
            timeout=20
        )
        resp.raise_for_status()
        data = resp.content
        self.write_to_file(file_path, data)
        return data

    def fetch_entity(self, piket, entity_id, modified_seconds):
        file_path = "%s/%s.xml" % (self.path, entity_id)
        try:
            info = os.lstat(file_path)
            # Check if the filesize is at least bigger than one byte
            if info.st_size < 2:
                raise OSError
        except OSError:
            # File does not exist, so let's download
            return self.download_entity(file_path, entity_id)

        # File already exists, check if newer
        if modified_seconds > self.get_entity_last_update(piket, entity_id):
            return self.download_entity(file_path, entity_id)

        # Return the local file if force_old_files is enabled
        elif self.source_definition.get('force_old_files'):
            f = open(file_path, 'r')
            data = f.read()
            f.close()
            return data

    @staticmethod
    def write_to_file(file_path, data):
        f = open(file_path, "w")
        f.write(data)
        f.close()

    @staticmethod
    def url_to_piket(url):
        return parse_qs(urlparse(url).query)['piket'][0]

    def piket_to_url(self, piket):
        if not piket:
            return self.feed_url

        url = urlparse(self.feed_url)
        qs = parse_qs(url.query)
        qs['piket'] = [piket]

        url = list(url)
        url[4] = urlencode(qs, doseq=True)
        return urlunparse(url)

    def get_last_pikets(self):
        result = self.redis.lrange('%s_piketten' % self.url_hash, -2, -1)
        try:
            second_last_piket, last_piket = result
            return second_last_piket, last_piket
        except ValueError:
            try:
                return '', result[0]
            except IndexError:
                return '', ''

    def get_pikets(self):
        return self.redis.lrange('%s_piketten' % self.url_hash, 0, -1)

    def push_piket(self, piket):
        self.redis.rpush('%s_piketten' % self.url_hash, piket)

    def push_entity(self, piket, entity_id, modified_seconds):
        self.redis.hmset('%s:%s' % (self.url_hash, piket),
                         {entity_id: int(modified_seconds)})

    def get_piket_entities(self, piket):
        return self.redis.hgetall('%s:%s' % (self.url_hash, piket))

    def get_entity_last_update(self, piket, entity_id):
        return self.redis.hget('%s:%s' % (self.url_hash, piket), entity_id)
