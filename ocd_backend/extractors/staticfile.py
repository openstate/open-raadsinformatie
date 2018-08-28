import gzip
import json
import os

from click import progressbar
from lxml import etree

from ocd_backend.exceptions import ConfigurationError
from ocd_backend.extractors import BaseExtractor, HttpRequestMixin


class StaticFileBaseExtractor(BaseExtractor, HttpRequestMixin):
    """ A base class for implementing extractors that retrieve items
    by fetching a single statically hosted external file."""

    def __init__(self, *args, **kwargs):
        super(StaticFileBaseExtractor, self).__init__(*args, **kwargs)

        if 'file_url' not in self.source_definition:
            raise ConfigurationError('Missing \'file_url\' definition')

        if not self.source_definition['file_url']:
            raise ConfigurationError('The \'file_url\' is empty')

        self.file_url = self.source_definition['file_url']

    def extract_items(self, static_content):
        """Parses the static content and extracts the items.

        This method must be implemented by the class that inherits the
        :py:class:`StaticFileBaseExtractor` and should return a generator
        that yields an item per iteration. Items should be formatted
        as tuples containing the following elements (in this order):

        - the content-type of the data retrieved from the source (e.g.
          ``application/json``)
        - the data in it's original format, as retrieved from the source
          (as a string)

        :param static_content: the retrieved static content containing
                               the items.
        :type static_content: str.
        """
        raise NotImplementedError

    def run(self):
        # Retrieve the static content from the source
        # TODO: disable ssl verification fro now since the
        # almanak implementation (of ssl) is broken.

        try:
            r = self.http_session.get(self.file_url, verify=False)
            static_content = r.content
        except Exception:
            static_content = u''

        # Extract and yield the items
        if static_content != '':
            for item in self.extract_items(static_content):
                yield item


class StaticXmlExtractor(StaticFileBaseExtractor):
    """Extract items from a single static XML file.

    The XPath expression used to extract items from the retrieved
    XML file should be specified in the definition of the source
    by populating the ``item_xpath`` attribute.
    """

    def __init__(self, *args, **kwargs):
        super(StaticXmlExtractor, self).__init__(*args, **kwargs)

        if 'item_xpath' not in self.source_definition:
            raise ConfigurationError('Missing \'item_xpath\' definition')

        if not self.source_definition['item_xpath']:
            raise ConfigurationError('The \'item_xpath\' is empty')

        self.item_xpath = self.source_definition['item_xpath']

        self.default_namespace = None
        if 'default_namespace' in self.source_definition:
            self.default_namespace = self.source_definition[
                'default_namespace'
            ]

    def extract_items(self, static_content):
        tree = etree.fromstring(static_content)

        namespaces = None
        if self.default_namespace is not None:
            # the namespace map has a key None if there is a default namespace
            # so the configuration has to specify the default key
            # xpath queries do not allow an empty default namespace
            self.namespaces = tree.nsmap
            try:
                self.namespaces[self.default_namespace] = self.namespaces[None]
                del self.namespaces[None]
            except KeyError as e:
                pass

        for item in tree.xpath(self.item_xpath, namespaces=self.namespaces):
            yield 'application/xml', etree.tostring(item)


class StaticHtmlExtractor(StaticFileBaseExtractor):
    """Extract items from a single static HTML file.

    The XPath expression used to extract items from the retrieved
    HTML file should be specified in the definition of the source
    by populating the ``item_xpath`` attribute.
    """

    def __init__(self, *args, **kwargs):
        super(StaticHtmlExtractor, self).__init__(*args, **kwargs)

        if 'item_xpath' not in self.source_definition:
            raise ConfigurationError('Missing \'item_xpath\' definition')

        if not self.source_definition['item_xpath']:
            raise ConfigurationError('The \'item_xpath\' is empty')

        self.item_xpath = self.source_definition['item_xpath']

        self.default_namespace = None
        if 'default_namespace' in self.source_definition:
            self.default_namespace = self.source_definition[
                'default_namespace'
            ]

    def extract_items(self, static_content):
        tree = etree.HTML(static_content)

        self.namespaces = None
        if self.default_namespace is not None:
            # the namespace map has a key None if there is a default namespace
            # so the configuration has to specify the default key
            # xpath queries do not allow an empty default namespace
            self.namespaces = tree.nsmap
            try:
                self.namespaces[self.default_namespace] = self.namespaces[None]
                del self.namespaces[None]
            except KeyError as e:
                pass

        for item in tree.xpath(self.item_xpath, namespaces=self.namespaces):
            yield 'application/html', etree.tostring(item)


class StaticJSONExtractor(StaticFileBaseExtractor):
    """
    Extract items from JSON files.
    """

    def extract_items(self, static_content):
        """
        Extracts items from a JSON file. It is assumed to be an array
        of items.
        """
        static_json = json.loads(static_content)

        for item in static_json:
            yield 'application/json', json.dumps(item)


class StaticJSONDumpExtractor(BaseExtractor):
    """
    Extract items from JSON dumps.
    """

    def __init__(self, *args, **kwargs):
        super(StaticJSONDumpExtractor, self).__init__(*args, **kwargs)

        if not self.source_definition.get('dump_path'):
            raise ConfigurationError('Missing \'dump_path\' definition')

    def run(self):
        """
        Override ``run`` as we don't have a HTTP request context
        :return:
        """
        dump_path = self.source_definition.get('dump_path')
        for item in self.extract_items(dump_path):
            yield item

    @staticmethod
    def extract_items(dump_path):
        if not os.path.isabs(dump_path):
            dump_path = os.path.abspath(dump_path)

        try:
            with progressbar(
                    gzip.open(dump_path, 'rb'), label='Loading %s' % dump_path
            ) as data:
                for line in data:
                    yield 'application/json', line.strip()
        except IOError:
            with open(dump_path, 'r') as f:
                data = json.load(f)
            for line in data:
                yield 'application/json', json.dumps(line)
