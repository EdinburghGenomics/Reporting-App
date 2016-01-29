__author__ = 'mwham'
from tests import Helper
from config import reporting_app_config, col_mappings
import reporting_app


class TestBase(Helper):
    def setUp(self):
        self.cfg = reporting_app_config
        self.col_mappings = col_mappings


class TestReportingApp(TestBase):

    def test_rest_query(self):
        q = reporting_app.rest_query(
            'test_resource',
            this='that',
            dict_query='{"other":1}',
        )
        expected = self.cfg['rest_api'] + '/test_resource?this=that&dict_query={"other":1}'
        assert len(q) == len(expected)

        q_base, q_query = q.split('?')
        e_base, e_query = expected.split('?')

        assert q_base == e_base
        assert sorted(q_query.split('&')) == sorted(e_query.split('&'))

    def test_distinct_values(self):
        input_json = [
            {'this': 0, 'that': 2},
            {'this': 4, 'that': 1},
            {'this': 8, 'that': 6},
            {'this': 5, 'that': 9}
        ]
        assert reporting_app._distinct_values('this', input_json) == [0, 4, 5, 8]
