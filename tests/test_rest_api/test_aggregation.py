__author__ = 'mwham'
import rest_api
from tests.test_rest_api import TestBase
import json
import os.path
from unittest.mock import patch, Mock
from collections import defaultdict


class FakeMongoClient(Mock):
    def __init__(self, host, port):
        super().__init__()
        self.host, self.port = host, port
        self.dbs = defaultdict(str)

    def __getitem__(self, item):
        return self.dbs[item]


with patch('pymongo.MongoClient', new=FakeMongoClient):
    import rest_api.aggregation.database_side


class TestAggregation(TestBase):
    def _json_test_file(self, pre_or_post, filename):
        return open(os.path.join(self.assets_dir, 'json', pre_or_post + '_aggregation', filename))

    def _compare_jsons(self, o, e):
        for x in (o, e):
            for y in ('run_ids',):
                self._reorder_comma_sep_list(x['data'], y)

        if o != e:
            print('!o_eq_e')
            for x, y in zip(e['data'], o['data']):
                missing = [k for k in x if k not in y]
                if missing:
                    print('missing expected key:')
                    print(missing)
            for x, y in zip(e['data'], o['data']):
                unexpected = [k for k in y if k not in x]
                if unexpected:
                    print('unexpected key:')
                    print(unexpected)
            for x, y in zip(e['data'], o['data']):
                different_values = ['%s: %s != %s'%(k, x[k], y[k]) for k in set(x).intersection(set(y)) if x[k] != y[k]]
                if different_values:
                    print('different values:')
                    print(different_values)
            raise AssertionError

    def _reorder_comma_sep_list(self, data, key):
        for e in data:
            if key not in e:
                continue
            if type(e[key]) is list:
                e[key] = list(sorted(e[key]))

    def _test_aggregation(self, aggregate, filename):
        raise NotImplementedError


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
            rest_api.aggregate_embedded_run_elements,
            'lanes_embedded_run_elements.json'
        )

    def test_embed_run_elements_into_samples(self):
        self._test_aggregation(
            rest_api.embed_run_elements_into_samples,
            'samples_embedded_run_elements.json',
            sort='-user_sample_id'
        )

    def test_run_element_basic_aggregation(self):
        self._test_aggregation(
            rest_api.run_element_basic_aggregation,
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

    def _test_aggregation(self, aggregate, filename, incomplete=False):
        if incomplete:
            filename += '_incomplete'
        filename += '.json'
        print()
        print(filename)
        self._compare_jsons(
            json.loads(aggregate(json.load(self._json_test_file('pre', filename)))),
            json.load(self._json_test_file('post', filename))
        )

    def test_aggregations_complete_data(self):
        for method, filename in (
            (rest_api.aggregation.server_side.run_element_basic_aggregation, 'run_elements_basic'),
            (rest_api.aggregation.server_side.aggregate_samples, 'samples_embedded_run_elements'),
            (rest_api.aggregation.server_side.aggregate_lanes, 'lanes_embedded_run_elements')
        ):
            self._test_aggregation(method, filename)

    def test_aggregations_incomplete_data(self):
        for method, filename in (
            #TODO rewrite these tests with more fine grain assertion
            #(rest_api.aggregation.server_side.run_element_basic_aggregation, 'run_elements_basic'),
            #(rest_api.aggregation.server_side.aggregate_samples, 'samples_embedded_run_elements'),
            #(rest_api.aggregation.server_side.aggregate_lanes, 'lanes_embedded_run_elements')
        ):
            self._test_aggregation(method, filename, incomplete=True)

    def test_aggregate_single_run_element(self):
        input_json = json.load(self._json_test_file('pre', 'run_elements_basic.json'))

        for e in input_json['data']:
            e.update(rest_api.aggregation.server_side._aggregate_run_element(e))

        expected = json.load(self._json_test_file('post', 'run_elements_basic.json'))
        assert input_json == expected

    def test_aggregate_single_run_element_incomplete(self):
        input_json = json.load(self._json_test_file('pre', 'run_elements_basic_incomplete.json'))

        for e in input_json['data']:
            e.update(rest_api.aggregation.server_side._aggregate_run_element(e))

        expected = json.load(self._json_test_file('post', 'run_elements_basic_incomplete.json'))
        assert input_json == expected

    def test_order_json(self):
        order = rest_api.aggregation.server_side._order_json
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


class TestDatabaseSide(TestBase):
    pass


class FakePayload:
    def __init__(self, data):
        self.data = data


class FakeRequest:
    def __init__(self, args):
        self.args = args
