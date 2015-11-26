__author__ = 'mwham'
import rest_api
from tests.test_rest_api import TestBase
import json
import os.path


class TestRestSide(TestBase):

    def _test_aggregation(self, aggregate, filename, sort=None):
        input_json = open(os.path.join(self.assets_dir, 'json', 'pre_aggregation', filename), 'rb').read()
        expected = open(os.path.join(self.assets_dir, 'json', 'post_aggregation', filename), 'rb').read()

        rq_args = {'embedded': '{"run_elements":1}'}
        if sort:
            rq_args['sort'] = sort
        request = FakeRequest(rq_args)
        payload = FakePayload(input_json)

        aggregate(request, payload)

        o = json.loads(payload.data.decode('utf-8'))
        e = json.loads(expected.decode('utf-8'))

        for x in (o, e):
            try:
                for d in x['data']:
                    d['run_ids'] = sorted(d['run_ids'].split(', '))
            except KeyError:
                pass

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


class TestServerSide(TestBase):
    def test(self):
        assert False


class TestDatabaseSide(TestBase):
    def test(self):
        assert False


class FakePayload:
    def __init__(self, data):
        self.data = data


class FakeRequest:
    def __init__(self, args):
        self.args = args
