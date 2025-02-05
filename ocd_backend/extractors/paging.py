from lxml import etree

from ocd_backend.exceptions import ConfigurationError
from ocd_backend.extractors.staticfile import StaticHtmlExtractor
from ocd_backend.log import get_source_logger

log = get_source_logger('extractor')


class PagingHTMLExtractor(StaticHtmlExtractor):
    def __init__(self, *args, **kwargs):
        super(PagingHTMLExtractor, self).__init__(*args, **kwargs)

        if 'next_page_xpath' not in self.source_definition:
            raise ConfigurationError('Missing \'next_page_xpath\' definition')

        if not self.source_definition['next_page_xpath']:
            raise ConfigurationError('The \'next_page_xpath\' is empty')

        self.next_page_xpath = self.source_definition['next_page_xpath']

        # default max 5 pages
        self.next_page_max_count = self.source_definition.get('next_page_max_count', 5)

    def get_next_url(self, static_content):
        tree = etree.HTML(static_content)
        next_page_elems = tree.xpath(self.next_page_xpath)
        if len(next_page_elems) > 0:
            return ''.join(next_page_elems[0])
        return 0

    def run(self):
        next_url = self.file_url
        next_page_count = 0
        while next_url is not None:
            log.info('Getting %s' % (next_url,))

            # Retrieve the static content from the source
            try:
                r = self.http_session.get(next_url, timeout=(3, 15), verify=False)
                static_content = r.content
            except Exception:
                static_content = ''

            next_page_count += 1

            # Extract and yield the items
            if static_content != '':
                for item in self.extract_items(static_content):
                    yield item
                if next_page_count < self.next_page_max_count:
                    next_url = self.get_next_url(static_content)
                else:
                    log.info('Max pages reached')
                    next_url = None
            else:
                next_url = None
