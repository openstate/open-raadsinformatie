import json
import mock
import random
from unittest import TestCase as UnittestTestCase
from pprint import pprint
import requests

from flask import url_for, current_app
from flask.ext.testing import TestCase

from ocd_frontend.rest import tasks
from .mixins import OcdRestTestCaseMixin


class RestApiSearchTestCase(OcdRestTestCaseMixin, TestCase):
    endpoint_url = 'api.search'
    endpoint_url_args = {}
    required_indexes = [
        'ori_test_combined_index'
    ]

    def test_valid_search(self):
        """Tests if a valid search request responds with a JSON and
        status 200 OK."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)
        print(url)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de'}))
        self.assert_ok_json(response)

    def test_missing_query(self):
        """Tests if a 200 response is returned when the required
        ``query`` attribute is missing."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'not-a-query': 'de'}))
        self.assert_ok(response)

    def test_sort_option_is_accepted(self):
        """Tests if valid use of the ``sort`` option results in a
        JSON response with a 200 OK."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)
        sort_field = random.choice(current_app.config['SORTABLE_FIELDS']['items'])
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de',
                                              'sort': sort_field}))
        self.assert_ok_json(response)

    def test_sort_order_option_is_accepted(self):
        """Test if valid use of the ``sort`` and ``order`` options
        result in a JSON response with a 200 OK."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)
        sort_field = random.choice(current_app.config['SORTABLE_FIELDS']['items'])
        sort_order = random.choice(['asc', 'desc'])
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de',
                                              'order': sort_order,
                                              'sort': sort_field}))
        self.assert_ok_json(response)

    def test_sort_option_with_invalid_field(self):
        """Tests if sorting on an invalid field results in a response
        with status code 400."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de',
                                              'sort': 'not-a-sort-field'}))
        self.assert_bad_request_json(response)

    def test_sort_option_with_invalid_order(self):
        """Test if supplying an invalid order option results in a
        response with status code 400."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)
        sort_field = random.choice(current_app.config['SORTABLE_FIELDS']['items'])
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de',
                                              'order': 'upsidedown',
                                              'sort': sort_field}))
        self.assert_bad_request_json(response)

    def test_facets(self):
        """Test if requesting facets results in a 200 OK, and if the
        facets are actually present in the response."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)
        available_facets = current_app.config['AVAILABLE_FACETS']
        facet_keys = random.sample(available_facets['items'].keys(), 1)
        facets = {fk: available_facets['items'][fk] for fk in facet_keys}

        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de',
                                              'facets': facets}))

        self.assert_ok_json(response)
        self.assertIn(u'facets', response.json)
        for fk in facet_keys:
            self.assertIn(fk, response.json.get(u'facets', {}))

    def test_invalid_facet_option_value(self):
        """Tests if requesting a facet with invalid value (not dict)
        results in a response with status code 400."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)

        facets = {
            'rights': []
        }

        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de',
                                              'facets': facets}))
        self.assert_bad_request_json(response)

    def test_not_available_facet(self):
        """Tests if requesting a facet that is not available results
        in a response with status code 400."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)

        facets = {
            'rights-that-are-not-a-facet': {}
        }

        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de',
                                              'facets': facets}))
        self.assert_bad_request_json(response)

    def test_facet_size(self):
        """Tests if valid use of the facet ``size`` attribute results in
        a 200 OK JSON response."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)

        facets = {
            'classification': {
                'size': 10
            }
        }

        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de',
                                              'facets': facets}))
        self.assert_ok_json(response)

    def test_invalid_facet_size(self):
        """Tests if supplying an invalid facet ``size`` value results in
        a response with status code 400."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)

        facets = {
            'source': {
                'size': 'abc'
            }
        }

        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de',
                                              'facets': facets}))
        self.assert_bad_request_json(response)

    # def test_datetime_facet(self):
    #     """Tests if valid use of the ``date`` facet results in a 200 OK
    #     JSON response."""
    #     url = url_for(self.endpoint_url, **self.endpoint_url_args)
    #
    #     facets = {
    #         'date': {
    #             'interval': 'month'
    #         }
    #     }
    #
    #     response = self.post(url, content_type='application/json',
    #                          data=json.dumps({'query': 'de',
    #                                           'facets': facets}))
    #     self.assert_ok_json(response)
    #     self.assertEqual(response.json['facets']['date']['_type'],
    #                      'date_histogram')

    def test_datetime_facet_interval_not_string(self):
        """Test if supplying an invalid interval type (i.e. integer)
        results in a response with status code 400."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)

        facets = {
            'date': {
                'date_histogram': {
                    'interval': 123
                }
            }
        }

        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de',
                                              'facets': facets}))
        self.assert_bad_request_json(response)

    def test_datetime_facet_interval_not_allowed(self):
        """Tests if supplying an invalid interval size results in
        a response with a status code 400."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)

        facets = {
            'date': {
                'date_histogram': {
                    'interval': 'millennium'
                }
            }
        }

        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de',
                                              'facets': facets}))
        self.assert_bad_request_json(response)

    def test_facet_should_be_dict(self):
        """Tests if supplying a list as facet request description
        results in a response with status code 400."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)
        facets = ['some facet']
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de',
                                              'facets': facets}))
        self.assert_bad_request_json(response)

    def test_from(self):
        """Test if setting the ``from`` attribute responds with JSON
        and status 200 OK."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de', 'from': 10}))
        self.assert_ok_json(response)

    def test_invalid_value_from(self):
        """Tests if supplying an invalid data type for the ``from``
        attribute results in a response with status code 400."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de', 'from': 'abc'}))
        self.assert_bad_request_json(response)

    def test_negative_value_from(self):
        """Test if supplying a negative value for the ``from`` attribute
        results in a response with status code 400."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de', 'from': -1}))
        self.assert_bad_request_json(response)

    def test_size(self):
        """Test if supplying a valid value for the ``size`` attribute
        results in a 200 OK JSON response."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de', 'size': 10}))
        self.assert_ok_json(response)

    def test_invalid_value_size(self):
        """Test if supplying an invalid type for the ``size`` attribute
        results in a response with status code 400."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de', 'size': 'abc'}))
        self.assert_bad_request_json(response)

    def test_negative_value_size(self):
        """Test if supplying a negative value for the ``size`` attribute
        results in a response with status code 400."""
        url = url_for(self.endpoint_url, **self.endpoint_url_args)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de', 'size': -1}))
        self.assert_bad_request_json(response)

    @mock.patch('ocd_frontend.rest.tasks.log_event.delay')
    def test_search_logging_called_if_enabled(self, mocked_log_task):
        """Test if the event log storage function is called when usage
        logging is enabled."""
        # Enable usage logging for this test
        self.app.config['USAGE_LOGGING_ENABLED'] = True

        # Make sure the Celery task doesn't get executed
        mocked_log_task.return_value = lambda *args, **kwargs: None

        url = url_for(self.endpoint_url, **self.endpoint_url_args)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de'}))
        self.assertTrue(mocked_log_task.called)

    @mock.patch('ocd_frontend.rest.tasks.log_event.delay')
    def test_search_logging_not_called_if_disabled(self, mocked_log_task):
        """Test if the event log storage function is not called when
        usage logging is disabled."""
        # Make sure usage logging is disabled
        self.app.config['USAGE_LOGGING_ENABLED'] = False

        # Make sure the Celery task doesn't get executed
        mocked_log_task.return_value = lambda *args, **kwargs: None

        url = url_for(self.endpoint_url, **self.endpoint_url_args)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de'}))
        self.assertFalse(mocked_log_task.called)


class RestApiSearchSourceTestCase(RestApiSearchTestCase):
    endpoint_url = 'api.search_source'
    endpoint_url_args = {'source_id': 'test_collection_index'}
    required_indexes = [
        'ori_test_collection_index'
    ]

    def test_nonexistent_source_id(self):
        """Test if supplying a nonexistent ``source_id`` returns a 404
        JSON response."""

        url = url_for(self.endpoint_url, source_id='i-do-not-exist')
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'query': 'de'}))
        self.assert_not_found_request_json(response)


class RestApiSearchSimilarTestCase(OcdRestTestCaseMixin, TestCase):
    required_indexes = [
        'ori_test_combined_index',
        'ori_test_collection_index'
    ]

    def test_valid_search(self):
        """Tests if a valid search request responds with a JSON and
        status 200 OK."""
        doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
        url = url_for('api.similar', object_id=doc_id)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({}))

        self.assert_ok_json(response)

    def test_valid_search_source(self):
        doc_id = self.doc_ids['ori_test_collection_index']['items'][0]
        url = url_for('api.similar', source_id='test_collection_index',
                      object_id=doc_id)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({}))

        self.assert_ok_json(response)

    def test_search_nonexistent_source(self):
        """Test if finding similar objects within a source index that
        doesn't  exist returns a 404 JSON response (with the appropriate
        error message)."""
        source_id = 'i-do-not-exist'
        doc_id = self.doc_ids['ori_test_collection_index']['items'][0]
        url = url_for('api.get_object', source_id=source_id, object_id=doc_id)
        response = self.get(url)

        self.assert_not_found_request_json(response)
        self.assertEqual(response.json['error'],
                         'Source \'%s\' does not exist' % source_id)

    def test_sort_option_is_accepted(self):
        """Tests if valid use of the ``sort`` option results in a
        JSON response with a 200 OK."""
        doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
        url = url_for('api.similar', object_id=doc_id)
        sort_field = random.choice(current_app.config['SORTABLE_FIELDS']['items'])
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'sort': sort_field}))
        self.assert_ok_json(response)

    def test_sort_order_option_is_accepted(self):
        """Test if valid use of the ``sort`` and ``order`` options
        result in a JSON response with a 200 OK."""
        doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
        url = url_for('api.similar', object_id=doc_id)
        sort_field = random.choice(current_app.config['SORTABLE_FIELDS']['items'])
        sort_order = random.choice(['asc', 'desc'])
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'order': sort_order,
                                              'sort': sort_field}))
        self.assert_ok_json(response)

    def test_sort_option_with_invalid_field(self):
        """Tests if sorting on an invalid field results in a response
        with status code 400."""
        doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
        url = url_for('api.similar', object_id=doc_id)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'sort': 'not-a-sort-field'}))
        self.assert_bad_request_json(response)

    def test_sort_option_with_invalid_order(self):
        """Test if supplying an invalid order option results in a
        response with status code 400."""
        doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
        url = url_for('api.similar', object_id=doc_id)
        sort_field = random.choice(current_app.config['SORTABLE_FIELDS']['items'])
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'order': 'upsidedown',
                                              'sort': sort_field}))
        self.assert_bad_request_json(response)

    # def test_facets(self):
    #     """Test if requesting facets results in a 200 OK, and if the
    #     facets are actually present in the response."""
    #     doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
    #     url = url_for('api.similar', object_id=doc_id)
    #
    #     available_facets = current_app.config['AVAILABLE_FACETS']
    #     facet_keys = random.sample(available_facets.keys(), 3)
    #     facets = {fk: available_facets[fk] for fk in facet_keys}
    #
    #     response = self.post(url, content_type='application/json',
    #                          data=json.dumps({'facets': facets}))
    #
    #     self.assert_ok_json(response)
    #     self.assertIn('facets', response.json)
    #     for fk in facet_keys:
    #         self.assertIn(fk, response.json.get('facets', {}))

    def test_not_available_facet(self):
        """Tests if requesting a facet that is not available results
        in a response with status code 400."""
        doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
        url = url_for('api.similar', object_id=doc_id)

        facets = {
            'rights-that-are-not-a-facet': {
                'terms': {
                    'field': 'meta.rights'
                }
            }
        }

        response = self.post(url, content_type='application/json',
                             data=json.dumps({'facets': facets}))
        self.assert_bad_request_json(response)

    def test_facet_size(self):
        """Tests if valid use of the facet ``size`` attribute results in
        a 200 OK JSON response."""
        doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
        url = url_for('api.similar', object_id=doc_id)

        facets = {
            'classification': {
                'size': 10
            }
        }

        response = self.post(url, content_type='application/json',
                             data=json.dumps({'facets': facets}))
        self.assert_ok_json(response)

    def test_invalid_facet_size(self):
        """Tests if supplying an invalid facet ``size`` value results in
        a response with status code 400."""
        doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
        url = url_for('api.similar', object_id=doc_id)

        facets = {
            'rights': {
                'size': 'abc'
            }
        }

        response = self.post(url, content_type='application/json',
                             data=json.dumps({'facets': facets}))
        self.assert_bad_request_json(response)

    # def test_datetime_facet(self):
    #     """Tests if valid use of the ``date`` facet results in a 200 OK
    #     JSON response."""
    #     doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
    #     url = url_for('api.similar', object_id=doc_id)
    #
    #     facets = {
    #         'date': {
    #             'date_histogram': {
    #                 'field': 'date',
    #                 'interval': 'month'
    #             }
    #         }
    #     }
    #
    #     response = self.post(url, content_type='application/json',
    #                          data=json.dumps({'facets': facets}))
    #     self.assert_ok_json(response)
    #     self.assertEqual(response.json['facets']['date']['_type'],
    #                      'date_histogram')
    #
    # def test_datetime_facet_interval_not_string(self):
    #     """Test if supplying an invalid interval type (i.e. integer)
    #     results in a response with status code 400."""
    #     doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
    #     url = url_for('api.similar', object_id=doc_id)
    #
    #     facets = {
    #         'date': {
    #             'date_histogram': {
    #                 'field': 'date',
    #                 'interval': 123
    #             }
    #         }
    #     }
    #
    #     response = self.post(url, content_type='application/json',
    #                          data=json.dumps({'facets': facets}))
    #     self.assert_bad_request_json(response)
    #
    # def test_datetime_facet_interval_not_allowed(self):
    #     """Tests if supplying an invalid interval size results in
    #     a response with a status code 400."""
    #     doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
    #     url = url_for('api.similar', object_id=doc_id)
    #
    #     facets = {
    #         'date': {
    #             'date_histogram': {
    #                 'field': 'date',
    #                 'interval': 'millennium'
    #             }
    #         }
    #     }
    #
    #     response = self.post(url, content_type='application/json',
    #                          data=json.dumps({'facets': facets}))
    #     self.assert_bad_request_json(response)

    def test_facet_should_be_dict(self):
        """Tests if supplying a list as facet request description
        results in a response with status code 400."""
        doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
        url = url_for('api.similar', object_id=doc_id)
        facets = ['some facet']
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'facets': facets}))
        self.assert_bad_request_json(response)

    def test_from(self):
        """Test if setting the ``from`` attribute responds with JSON
        and status 200 OK."""
        doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
        url = url_for('api.similar', object_id=doc_id)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'from': 10}))
        self.assert_ok_json(response)

    def test_invalid_value_from(self):
        """Tests if supplying an invalid data type for the ``from``
        attribute results in a response with status code 400."""
        doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
        url = url_for('api.similar', object_id=doc_id)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'from': 'abc'}))
        self.assert_bad_request_json(response)

    def test_negative_value_from(self):
        """Test if supplying a negative value for the ``from`` attribute
        results in a response with status code 400."""
        doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
        url = url_for('api.similar', object_id=doc_id)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'from': -1}))
        self.assert_bad_request_json(response)

    def test_size(self):
        """Test if supplying a valid value for the ``size`` attribute
        results in a 200 OK JSON response."""
        doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
        url = url_for('api.similar', object_id=doc_id)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'size': 10}))
        self.assert_ok_json(response)

    def test_invalid_value_size(self):
        """Test if supplying an invalid type for the ``size`` attribute
        results in a response with status code 400."""
        doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
        url = url_for('api.similar', object_id=doc_id)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'size': 'abc'}))
        self.assert_bad_request_json(response)

    def test_negative_value_size(self):
        """Test if supplying a negative value for the ``size`` attribute
        results in a response with status code 400."""
        doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
        url = url_for('api.similar', object_id=doc_id)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({'size': -1}))
        self.assert_bad_request_json(response)

    @mock.patch('ocd_frontend.rest.tasks.log_event.delay')
    def test_search_logging_called_if_enabled(self, mocked_log_task):
        """Test if the event log storage function is called when usage
        logging is enabled."""
        # Enable usage logging for this test
        self.app.config['USAGE_LOGGING_ENABLED'] = True

        # Make sure the Celery task doesn't get executed
        mocked_log_task.return_value = lambda *args, **kwargs: None

        doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
        url = url_for('api.similar', object_id=doc_id)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({}))
        self.assertTrue(mocked_log_task.called)

    @mock.patch('ocd_frontend.rest.tasks.log_event.delay')
    def test_search_logging_not_called_if_disabled(self, mocked_log_task):
        """Test if the event log storage function is not called when
        usage logging is disabled."""
        # Make sure usage logging is disabled
        self.app.config['USAGE_LOGGING_ENABLED'] = False

        # Make sure the Celery task doesn't get executed
        mocked_log_task.return_value = lambda *args, **kwargs: None

        doc_id = self.doc_ids['ori_test_combined_index']['item'][0]
        url = url_for('api.similar', object_id=doc_id)
        response = self.post(url, content_type='application/json',
                             data=json.dumps({}))
        self.assertFalse(mocked_log_task.called)

class RestApiSourcesTestCase(OcdRestTestCaseMixin, TestCase):
    required_indexes = [
        'ori_test_combined_index'
    ]

    def test_response_format(self):
        url = url_for('api.list_sources')
        response = self.get(url)

        self.assert_ok_json(response)

        self.assertIn('sources', response.json)

        source_attrs = response.json['sources'][0].keys()
        self.assertIn('id', source_attrs)
        self.assertIn('organizations', source_attrs)

    @mock.patch('ocd_frontend.rest.tasks.log_event.delay')
    def test_logging_called_if_enabled(self, mocked_log_task):
        """Test if the event log storage function is called when usage
        logging is enabled."""
        # Enable usage logging for this test
        self.app.config['USAGE_LOGGING_ENABLED'] = True

        # Make sure the Celery task doesn't get executed
        mocked_log_task.return_value = lambda *args, **kwargs: None

        url = url_for('api.list_sources')
        response = self.get(url)
        self.assertTrue(mocked_log_task.called)

    @mock.patch('ocd_frontend.rest.tasks.log_event.delay')
    def test_logging_not_called_if_disabled(self, mocked_log_task):
        """Test if the event log storage function is not called when
        usage logging is disabled."""
        # Make sure usage logging is disabled
        self.app.config['USAGE_LOGGING_ENABLED'] = False

        # Make sure the Celery task doesn't get executed
        mocked_log_task.return_value = lambda *args, **kwargs: None

        url = url_for('api.list_sources')
        response = self.get(url)
        self.assertFalse(mocked_log_task.called)


class RestApiGetObjectTestCase(OcdRestTestCaseMixin, TestCase):
    required_indexes = [
        'ori_test_collection_index'
    ]

    def test_get_existing_object(self):
        """Test getting an index document."""
        doc_id = self.doc_ids['ori_test_collection_index']['items'][0]
        url = url_for('api.get_object', source_id='test_collection_index',
                      object_id=doc_id)
        response = self.get(url)

        self.assert_ok_json(response)

    def test_get_nonexistent_object(self):
        """Test if getting an object that doesn't exist returns a 404
        JSON response (with the appropriate error message)."""
        url = url_for('api.get_object', source_id='test_collection_index',
                      object_id='i-do-not-exist')
        response = self.get(url)

        self.assert_not_found_request_json(response)
        self.assertEqual(response.json['error'], 'Document not found.')

    def test_get_nonexistent_source(self):
        """Test if getting an object from a source index that doesn't
        exist returns a 404 JSON response (with the appropriate error
        message)."""
        source_id = 'i-do-not-exist'
        url = url_for('api.get_object', source_id=source_id,
                      object_id='i-do-not-exist')
        response = self.get(url)

        self.assert_not_found_request_json(response)
        self.assertEqual(response.json['error'],
                         'Source \'%s\' does not exist' % source_id)

    @mock.patch('ocd_frontend.rest.tasks.log_event.delay')
    def test_logging_called_if_enabled(self, mocked_log_task):
        """Test if the event log storage function is called when usage
        logging is enabled."""
        # Enable usage logging for this test
        self.app.config['USAGE_LOGGING_ENABLED'] = True

        # Make sure the Celery task doesn't get executed
        mocked_log_task.return_value = lambda *args, **kwargs: None

        doc_id = self.doc_ids['ori_test_collection_index']['items'][0]
        url = url_for('api.get_object', source_id='test_collection_index',
                      object_id=doc_id)
        response = self.get(url)
        self.assertTrue(mocked_log_task.called)

    @mock.patch('ocd_frontend.rest.tasks.log_event.delay')
    def test_search_logging_not_called_if_disabled(self, mocked_log_task):
        """Test if the event log storage function is not called when
        usage logging is disabled."""
        # Make sure usage logging is disabled
        self.app.config['USAGE_LOGGING_ENABLED'] = False

        # Make sure the Celery task doesn't get executed
        mocked_log_task.return_value = lambda *args, **kwargs: None

        doc_id = self.doc_ids['ori_test_collection_index']['items'][0]
        url = url_for('api.get_object', source_id='test_collection_index',
                      object_id=doc_id)
        self.assertFalse(mocked_log_task.called)


class RestApiGetObjectSourceTestCase(OcdRestTestCaseMixin, TestCase):
    required_indexes = [
        'ori_test_collection_index'
    ]

    def test_get_existing_object(self):
        """Test getting an index document."""
        doc_id = self.doc_ids['ori_test_collection_index']['items'][0]
        url = url_for('api.get_object_source',
                      source_id='test_collection_index',
                      doc_type='items', object_id=doc_id)
        response = self.get(url)

        pprint(requests.get('http://localhost:9200/_cat/indices').content)
        pprint(self.doc_ids)
        pprint(url)
        pprint(response)
        self.assert_ok_json(response)

    def test_get_nonexistent_object(self):
        """Test if getting an object that doesn't exist returns a 404
        JSON response (with the appropriate error message)."""
        url = url_for('api.get_object_source',
                      source_id='test_collection_index',
                      object_id='i-do-not-exist')
        response = self.get(url)

        self.assert_not_found_request_json(response)
        self.assertEqual(response.json['error'], 'Document not found.')

    def test_get_nonexistent_source(self):
        """Test if getting an object from a source index that doesn't
        exist returns a 404 JSON response (with the appropriate error
        message)."""
        source_id = 'i-do-not-exist'
        url = url_for('api.get_object_source', source_id=source_id,
                      object_id='i-do-not-exist')
        response = self.get(url)

        self.assert_not_found_request_json(response)
        self.assertEqual(response.json['error'],
                         'Source \'%s\' does not exist' % source_id)

    @mock.patch('ocd_frontend.rest.tasks.log_event.delay')
    def test_logging_called_if_enabled(self, mocked_log_task):
        """Test if the event log storage function is called when usage
        logging is enabled."""
        # Enable usage logging for this test
        self.app.config['USAGE_LOGGING_ENABLED'] = True

        # Make sure the Celery task doesn't get executed
        mocked_log_task.return_value = lambda *args, **kwargs: None

        doc_id = self.doc_ids['ori_test_collection_index']['items'][0]
        url = url_for('api.get_object_source',
                      source_id='test_collection_index', object_id=doc_id)
        response = self.get(url)
        self.assertTrue(mocked_log_task.called)

    @mock.patch('ocd_frontend.rest.tasks.log_event.delay')
    def test_search_logging_not_called_if_disabled(self, mocked_log_task):
        """Test if the event log storage function is not called when
        usage logging is disabled."""
        # Make sure usage logging is disabled
        self.app.config['USAGE_LOGGING_ENABLED'] = False

        # Make sure the Celery task doesn't get executed
        mocked_log_task.return_value = lambda *args, **kwargs: None

        doc_id = self.doc_ids['ori_test_collection_index']['items'][0]
        url = url_for('api.get_object_source',
                      source_id='test_collection_index', object_id=doc_id)
        response = self.get(url)
        self.assertFalse(mocked_log_task.called)


class RestApiGetObjectStatsTestCaste(OcdRestTestCaseMixin, TestCase):
    required_indexes = [
        'ori_test_usage_logging_index',
        'ori_test_collection_index'
    ]

    def test_get_existing_object(self):
        """Test getting the stats of an indexed document."""
        doc_id = self.doc_ids['ori_test_collection_index']['items'][0]
        url = url_for('api.get_object_stats',
                      source_id='test_collection_index', object_id=doc_id)
        response = self.get(url)

        self.assert_ok_json(response)

    def test_get_nonexistent_object(self):
        """Test if getting an object that doesn't exist returns a 404
        JSON response."""
        url = url_for('api.get_object_source',
                      source_id='test_collection_index',
                      object_id='i-do-not-exist')
        response = self.get(url)

        self.assert_not_found_request_json(response)

    def test_get_nonexistent_source(self):
        """Test if getting an object from a source index that doesn't
        exist returns a 404 JSON response."""
        url = url_for('api.get_object_stats', source_id='i-do-not-exist',
                      object_id='i-do-not-exist')
        response = self.get(url)

        self.assert_not_found_request_json(response)


class RestApiResolveTestCase(OcdRestTestCaseMixin, TestCase):
    required_indexes = [
        'ori_test_resolver_index'
    ]

    def test_successful_resolve(self):
        """Test if a valid URL resolves and returns a redirect with the
        correct status, location and content type."""
        doc_id = self.doc_ids['ori_test_resolver_index']['url'][0]
        url = url_for('api.resolve', url_id=doc_id)

        response = self.get(url, follow_redirects=False)

        self.assert_status_code(response, 302)
        self.assert_content_type(response, 'text/html; charset=utf-8')
        self.assertIn('location', response.headers)
        self.assertTrue(response.headers['location'].startswith('http://'))

    def test_resolve_not_whitelisted_content_type(self):
        """Test that a resolve document with an incorrent content_type resolves
        to the original url"""
        doc_id = self.doc_ids['ori_test_resolver_index']['url'][1]
        url = url_for('api.resolve', url_id=doc_id)

        response = self.get(url, follow_redirects=False)

        self.assert_status_code(response, 302)
        self.assert_content_type(response, 'text/html; charset=utf-8')
        self.assertIn('location', response.headers)
        self.assertTrue(response.headers['location'].startswith('http://'))

    def test_successful_thumbnail_resolve(self):
        """Test if a valid URL resolves and returns a redirect to a thumbnailed
        image.
        """
        doc_id = self.doc_ids['ori_test_resolver_index']['url'][0]
        url = url_for('api.resolve', url_id=doc_id, size='large')

        response = self.get(url, follow_redirects=False)

        self.assert_status_code(response, 302)
        self.assert_content_type(response, 'text/html; charset=utf-8')
        self.assertIn('location', response.headers)
        self.assertIn('large', response.headers['location'])
        self.assertIn(self.app.config.get('THUMBNAIL_URL'), response.headers['location'])

    def test_invalid_thumbnail_size_json(self):
        """Test if a request with an invalid thumbnail size returns a 400 with
        proper content type"""
        doc_id = self.doc_ids['ori_test_resolver_index']['url'][0]
        url = url_for('api.resolve', url_id=doc_id, size='humongous')

        response = self.get(url, follow_redirects=False)

        self.assert_bad_request(response)
        self.assert_content_type(response, 'application/json')
        self.assertEqual(response.json.get('status'), 'error')
        self.assertIn('appropriate thumbnail size', response.json.get('error'))

    def test_invalid_thumbnail_size_html(self):
        """Test if a request with an invalid thumbnail size returns a 400 with
        proper content type"""
        doc_id = self.doc_ids['ori_test_resolver_index']['url'][0]
        url = url_for('api.resolve', url_id=doc_id, size='humongous')

        response = self.get(url, follow_redirects=False,
                            content_type='text/html')

        self.assert_bad_request(response)
        self.assert_content_type(response, 'text/html; charset=utf-8')
        self.assertIn('<html><body>You did not provide an appropriate '
                      'thumbnail size', response.data)

    def test_invalid_resolve_json(self):
        """Tests if a request to resolve an invalid URL results in a
        404 response with the proper content type."""
        url = url_for('api.resolve', url_id='i-do-not-exist')
        response = self.get(url, follow_redirects=False,
                            content_type='application/json')
        self.assert_not_found_request_json(response)


    def test_invalid_resolve_html(self):
        """Tests if a request to resolve an invalid URL results in a
        404 response with the proper content type."""
        url = url_for('api.resolve', url_id='i-do-not-exist')
        response = self.get(url, follow_redirects=False,
                            content_type='text/html')

        self.assert_not_found(response)
        self.assert_content_type(response, 'text/html; charset=utf-8')

    @mock.patch('ocd_frontend.rest.tasks.log_event.delay')
    def test_logging_called_if_enabled(self, mocked_log_task):
        """Test if the event log storage function is called when usage
        logging is enabled."""
        # Enable usage logging for this test
        self.app.config['USAGE_LOGGING_ENABLED'] = True

        # Make sure the Celery task doesn't get executed
        mocked_log_task.return_value = lambda *args, **kwargs: None

        doc_id = self.doc_ids['ori_test_resolver_index']['url'][0]
        url = url_for('api.resolve', url_id=doc_id)
        response = self.get(url, follow_redirects=False)

        self.assertTrue(mocked_log_task.called)

    @mock.patch('ocd_frontend.rest.tasks.log_event.delay')
    def test_search_logging_not_called_if_disabled(self, mocked_log_task):
        """Test if the event log storage function is not called when
        usage logging is disabled."""
        # Make sure usage logging is disabled
        self.app.config['USAGE_LOGGING_ENABLED'] = False

        # Make sure the Celery task doesn't get executed
        mocked_log_task.return_value = lambda *args, **kwargs: None

        doc_id = self.doc_ids['ori_test_resolver_index']['url'][0]
        url = url_for('api.resolve', url_id=doc_id)
        response = self.get(url,  follow_redirects=False)
        self.assertFalse(mocked_log_task.called)


class LogEventTaskTestCase(UnittestTestCase):
    default_args = {
        'user_agent': 'abc',
        'referer': 'def',
        'user_ip': '127.0.0.1',
        'created_at': '2015-01-01',
        'event_type': 'get_object'
    }

    def test_unknown_event_raises_exception(self):
        task_args = self.default_args
        task_args['event_type'] = 'unknown-test-event'
        self.assertRaises(ValueError, tasks.log_event, **task_args)
