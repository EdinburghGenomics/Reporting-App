import json
from datetime import datetime
from rest_api.aggregation import server_side
from tests.test_rest_api.test_aggregation import TestAggregation, FakeRequest


class FakePayload:
    def __init__(self, data):
        self.data = data


class TestRestSide(TestAggregation):
    def _test_aggregation(self, aggregate, filename, sort=None):
        input_json = json.load(self._json_test_file('pre', filename))

        rq_args = {'embedded': '{"run_elements":1}', 'aggregate': 'True'}
        if sort:
            rq_args['sort'] = sort
        request = FakeRequest(rq_args)
        payload = FakePayload(json.dumps(input_json).encode())

        aggregate(request, payload)

        self._compare_jsons(
            json.loads(payload.data.decode('utf-8')),
            json.load(self._json_test_file('post', filename))
        )

    def test_aggregate_embedded_run_elements(self):
        self._test_aggregation(
            server_side.aggregate_embedded_run_elements,
            'lanes_embedded_run_elements.json'
        )

    def test_embed_run_elements_into_samples(self):
        self._test_aggregation(
            server_side.embed_run_elements_into_samples,
            'samples_embedded_run_elements.json',
            sort='-user_sample_id'
        )

    def test_run_element_basic_aggregation(self):
        self._test_aggregation(
            server_side.run_element_basic_aggregation,
            'run_elements_basic.json'
        )


class TestServerSide(TestAggregation):
    test_data = {
        'data': [
            {'this': 2, 'that': 0, 'field_not_in_schema': 2},
            {'this': 6, 'that': 9, 'field_not_in_schema': 8},
            {'this': 8, 'that': 4, 'field_not_in_schema': 5},
            {'this': 1, 'that': 1, 'field_not_in_schema': 1},
            {'this': 3, 'that': 3, 'field_not_in_schema': 6}
        ],
        '_links': {
            'self': {
                'title': 'run_elements'
            }
        }
    }

    def _test_aggregation(self, aggregate, filename, incomplete=False, trim_run_elements=False):
        if incomplete:
            filename += '_incomplete'
        filename += '.json'
        self._compare_jsons(
            json.loads(server_side._aggregate_data(json.load(self._json_test_file('pre', filename)), aggregate, trim_run_elements=trim_run_elements)),
            json.load(self._json_test_file('post', filename))
        )

    def test_aggregations_complete_data(self):
        for method, filename, trim_run_elements in (
            (server_side._aggregate_run_element, 'run_elements_basic', False),
            (server_side._aggregate_sample, 'samples_embedded_run_elements', True),
            (server_side._aggregate_lane, 'lanes_embedded_run_elements', False)
        ):
            self._test_aggregation(method, filename, trim_run_elements=trim_run_elements)

    def test_aggregations_incomplete_data(self):
        for method, filename, trim_run_elements in (
            # TODO rewrite these tests with more fine grain assertion
            # (server_side._aggregate_run_element, 'run_elements_basic', False),
            # (server_side._aggregate_sample, 'samples_embedded_run_elements', True),
            # (server_side._aggregate_lane, 'lanes_embedded_run_elements', False)
        ):
            self._test_aggregation(method, filename, incomplete=True)

    def test_aggregate_single_run_element(self):
        input_json = json.load(self._json_test_file('pre', 'run_elements_basic.json'))

        for e in input_json['data']:
            e.update(server_side._aggregate_run_element(e))

        expected = json.load(self._json_test_file('post', 'run_elements_basic.json'))
        assert input_json == expected

    def test_aggregate_single_run_element_incomplete(self):
        input_json = json.load(self._json_test_file('pre', 'run_elements_basic_incomplete.json'))

        for e in input_json['data']:
            e.update(server_side._aggregate_run_element(e))

        expected = json.load(self._json_test_file('post', 'run_elements_basic_incomplete.json'))
        assert input_json == expected

    def test_order_json(self):
        order = server_side._order_json
        j = self.test_data
        nosort = json.loads(order(j))
        assert nosort == j

        ascsort = json.loads(order(j, sortquery='field_not_in_schema'))['data']
        descsort = json.loads(order(j, sortquery='-field_not_in_schema'))['data']

        assert ascsort == [
            {'this': 1, 'that': 1, 'field_not_in_schema': 1},
            {'this': 2, 'that': 0, 'field_not_in_schema': 2},
            {'this': 8, 'that': 4, 'field_not_in_schema': 5},
            {'this': 3, 'that': 3, 'field_not_in_schema': 6},
            {'this': 6, 'that': 9, 'field_not_in_schema': 8}
        ]
        assert descsort == list(reversed(ascsort))


class TestPostProcessing(TestAggregation):
    def test_cast_to_sets(self):
        p = server_side.post_processing.cast_to_sets('column_to_cast')
        agg = [
            {'column_to_cast': ['this', 'that', 'other', 'this', 'this', 'that']},
            {'column_to_cast': ['another', 'more', 'another', 'that']}
        ]
        assert p(agg) == [
            {'column_to_cast': {'this', 'that', 'other'}},
            {'column_to_cast': {'that', 'another', 'more'}}
        ]

    def test_date_to_string(self):
        p = server_side.post_processing.date_to_string('_created')
        agg = [
            {'_created': datetime(2016, 4, 13, 12, 0, 0)},
            {'_created': datetime(2016, 4, 13, 12, 10, 0)}
        ]
        assert p(agg) == [
            {'_created': '2016-04-13 12:00:00'},
            {'_created': '2016-04-13 12:10:00'}
        ]
