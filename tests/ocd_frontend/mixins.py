import json
import os
import shutil
from glob import glob

from werkzeug.utils import parse_cookie

import ocd_frontend


class OcdRestTestCaseMixin(object):
    required_indexes = []

    def create_app(self):
        """Create instance of Flask application for testing."""

        app = ocd_frontend.rest.create_app()
        app.config['TESTING'] = True
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        app.config['COMBINED_INDEX'] = 'ori_test_combined_index'
        app.config['RESOLVER_URL_INDEX'] = 'ori_test_resolver_index'
        app.config['USAGE_LOGGING_INDEX'] = 'ori_test_usage_logging_index'
        app.config['USAGE_LOGGING_ENABLED'] = False

        self.es_client = app.es.get_esclient()
        self.PWD = os.path.dirname(__file__)
        self.thumbnail_cache = os.path.join(os.path.abspath(self.PWD),
                                            'test-thumbnail-cache')

        app.config['THUMBNAIL_DIR'] = self.thumbnail_cache

        return app

    def setup(self):
        # If ES indexes are required, Elasticsearch should be running
        if self.required_indexes:
            self.assertTrue(self.es_client.ping(),
                            msg='Elasticsearch cluster is not running')

        # Add the specified Elasticsearch indexes
        self.es_add_indices(self.required_indexes)

        # Add test documents to the specified indexes
        self.es_index_docs(self.required_indexes)

        self.create_thumbnail_cache()

    def create_thumbnail_cache(self):
        os.makedirs(self.thumbnail_cache)
        self.addCleanup(self.remove_thumbnail_cache)

    def es_add_indices(self, indices):
        """Create the ES indexes givin in ``indices``. A cleanup
        also registered for each index."""

        for index in indices:
            if not self.es_client.indices.exists(index):
                self.es_client.indices.create(index)
                self.addCleanup(self.es_remove_index, index)

    def es_index_docs(self, indices):
        """Index test documents for each index specified in ``indices``."""

        # Put the IDs of the indexed docs in a dict that is grouped by
        # index so the tests can you it to fecth sample docs by ID
        self.doc_ids = {}

        for index in indices:
            self.doc_ids[index] = {}

            files_path = os.path.join(self.PWD, 'test_data', index, '*.json')
            test_file_paths = glob(files_path)

            for doc_file_path in test_file_paths:
                # The doc_type is determined by the first part of the filename
                doc_type = os.path.split(doc_file_path)[-1].split('_')[0]

                with open(doc_file_path, 'rb') as doc_file:
                    doc = json.load(doc_file)

                    # Explicitly refresh index, as the upcoming count
                    # request can be faster to execute than the refresh
                    # rate of the ES instance
                    i_doc = self.es_client.index(index=index, body=doc,
                                                 doc_type=doc_type,
                                                 refresh=True)

                    if doc_type not in self.doc_ids[index]:
                        self.doc_ids[index][doc_type] = []
                    self.doc_ids[index][doc_type].append(i_doc['_id'])

            self.assertEqual(
                self.es_client.count(index=index).get('count'),
                len(test_file_paths),
                msg='Incorrect doc count in ES index %s' % index
            )

    def es_remove_index(self, index_name):
        self.es_client.indices.delete(index_name)

    def remove_thumbnail_cache(self):
        """Remove thumbnail cache directory"""
        shutil.rmtree(self.thumbnail_cache)

    @staticmethod
    def _request(method, *args, **kwargs):
        """Execute HTTP method with provided args and kwargs.

        The ``content_type`` is set to "application/json" by default,
        as the API expects JSON in most requests. Also, the test cases
        should follow redirects by default.

        :param method: HTTP method to use (i.e. 'get', 'post', 'put', etc.)
        :return:
        """
        kwargs.setdefault('content_type', 'application/json')
        kwargs.setdefault('follow_redirects', True)
        return method(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self._request(self.client.get, *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._request(self.client.post, *args, **kwargs)

    def put(self, *args, **kwargs):
        return self._request(self.client.put, *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._request(self.client.delete, *args, **kwargs)

    @staticmethod
    def get_cookies(response):
        """Parse cookies from Flask Response.

        :param response:
        :return: dict with cookie values
        """
        cookies = {}
        for value in response.headers.get_all('Set-Cookie'):
            cookies.update(parse_cookie(value))
        return cookies

    def assert_status_code(self, response, status_code):
        """Assert status code of a Flask test client response

        :param response: test client response object
        :param status_code: expected status code
        :return: Flask.Response
        """
        self.assertEquals(status_code, response.status_code)
        return response

    def assert_content_type(self, response, content_type):
        """Assert the content-type of a Flask test client response

        :param response: The test client response object
        :param content_type: The expected content type
        :return: Flask.Response
        """
        self.assertEquals(content_type, response.headers.get('Content-Type'))
        return response

    def assert_ok(self, response):
        return self.assert_status_code(response, 200)

    def assert_bad_request(self, response):
        return self.assert_status_code(response, 400)

    def assert_unauthorized(self, response):
        return self.assert_status_code(response, 401)

    def assert_forbidden(self, response):
        return self.assert_status_code(response, 403)

    def assert_not_found(self, response):
        return self.assert_status_code(response, 404)

    def assert_json(self, response):
        """JSON response

        :param response: Flask.Response
        :return: Flask.Response
        """
        return self.assert_content_type(response, 'application/json')

    def assert_ok_html(self, response):
        """200 OK HTML response

        :param response: Flask.Response
        :return: Flask.Response
        """
        return self.assert_ok(
            self.assert_content_type(response, 'text/html; charset=utf-8')
        )

    def assert_ok_json(self, response):
        """200 OK JSON response

        :param response: Flask.Response
        :return: Flask.Response
        """
        return self.assert_ok(self.assert_json(response))

    def assert_bad_request_json(self, response):
        """Assert 400 Bad Request JSON response

        :param response: Flask.Response
        :return: Flask.Response
        """
        return self.assert_bad_request(self.assert_json(response))

    def assert_not_found_request_json(self, response):
        """Assert 404 Not Founrd JSON response

        :param response: Flask.Response
        :return: Flask.Response
        """
        return self.assert_not_found(self.assert_json(response))
