__author__ = 'mwham'
from tests.test_rest_api import TestBase
import rest_api


class TestRestAPI(TestBase):

    def test_from_query_string(self):
        test_query = {'embedded': '{"this_field":1,"that_field":2}', 'sort': '-other_field'}

        expected_embedding = '{"this_field":1,"that_field":2}'
        assert rest_api._from_query_string(test_query, 'embedded') == expected_embedding

        assert rest_api._from_query_string(test_query, 'sort', json=False) == '-other_field'
