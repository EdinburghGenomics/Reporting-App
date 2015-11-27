__author__ = 'mwham'
import rest_api
from tests.test_rest_api import TestBase
import json
import os.path


class TestAggregation(TestBase):
    def _test_json(self, pre_or_post, filename):
        return open(os.path.join(self.assets_dir, 'json', pre_or_post + '_aggregation', filename))

    def _reorder_comma_sep_list(self, data, key):
        try:
            for e in data:
                e[key] = sorted(e[key].split(', '))
        except KeyError:
            pass


class TestRestSide(TestAggregation):

    def _test_aggregation(self, aggregate, filename, sort=None):
        input_json = json.load(self._test_json('pre', filename))

        rq_args = {'embedded': '{"run_elements":1}'}
        if sort:
            rq_args['sort'] = sort
        request = FakeRequest(rq_args)
        payload = FakePayload(json.dumps(input_json).encode())

        aggregate(request, payload)

        o = json.loads(payload.data.decode('utf-8'))
        e = json.load(self._test_json('post', filename))

        for x in (o, e):
            self._reorder_comma_sep_list(x['data'], 'run_ids')
        assert o == e

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

    def _compare_jsons(self, aggregate, filename):
        o = json.loads(aggregate(json.load(self._test_json('pre', filename))))
        e = json.load(self._test_json('post', filename))
        for x in (o, e):
            self._reorder_comma_sep_list(x['data'], 'run_ids')
        assert o == e

    # def test_sum(self):
    #     assert rest_api.aggregation.server_side._sum(self.test_data['data'], 'this') == 20
    #
    # def test_percentage(self):
    #     assert rest_api.aggregation.server_side._percentage(self.test_data['data'][2], ('that', 'this')) == 50

    def test_run_element_basic_aggregation(self):
        self._compare_jsons(
            rest_api.aggregation.server_side.run_element_basic_aggregation,
            'run_elements_basic.json'
        )

    def test_aggregate_samples(self):
        self._compare_jsons(
            rest_api.aggregation.server_side.aggregate_samples,
            'samples_embedded_run_elements.json'
        )

    def test_aggregate_lanes(self):
        self._compare_jsons(
            rest_api.aggregation.server_side.aggregate_lanes,
            'lanes_embedded_run_elements.json'
        )

    # def test_aggregate_single_run_element(self):
    #     input_json = json.load(self._test_json('pre', 'run_elements_basic.json'))
    #
    #     for e in input_json['data']:
    #         rest_api.aggregation.server_side.aggregate_single_run_element(e)
    #
    #     expected = json.load(self._test_json('post', 'run_elements_basic.json'))
    #     assert input_json == expected

    def test_order_json(self):
        order = rest_api.aggregation.server_side.order_json
        j = self.test_data
        nosort = order(j)
        ascsort = order(j, sortquery='field_not_in_schema')['data']
        descsort = order(j, sortquery='-field_not_in_schema')['data']

        assert nosort == j
        assert ascsort == [
            {'this': 1, 'that': 1, 'field_not_in_schema': 1},
            {'this': 2, 'that': 0, 'field_not_in_schema': 2},
            {'this': 8, 'that': 4, 'field_not_in_schema': 5},
            {'this': 3, 'that': 3, 'field_not_in_schema': 6},
            {'this': 6, 'that': 9, 'field_not_in_schema': 8}
        ]
        assert descsort == list(reversed(ascsort))


class TestDatabaseSide(TestBase):
    def test_format_order(self):
        assert rest_api.aggregation.database_side.queries._format_order('thing') == {'thing': 1}
        assert rest_api.aggregation.database_side.queries._format_order('-thing') == {'thing': -1}


class FakePayload:
    def __init__(self, data):
        self.data = data


class FakeRequest:
    def __init__(self, args):
        self.args = args
