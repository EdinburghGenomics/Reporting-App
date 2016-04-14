from tests import Helper
from config import reporting_app_config, col_mappings
from reporting_app import util


class TestBase(Helper):
    def setUp(self):
        self.cfg = reporting_app_config
        self.col_mappings = col_mappings


class TestReportingApp(TestBase):
    def test_rest_query(self):
        q = util.rest_query(
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

    def test_format_order(self):
        cols = (
            {'name': 'this', 'title': 'This'},
            {'name': 'that', 'title': 'That'},
            {'name': 'other', 'title': 'Other'},
            {'name': 'another', 'title': 'Another'}
        )
        assert util._format_order('this', cols) == [0, 'asc']
        assert util._format_order('-other', cols) == [2, 'desc']

    def test_datatable_cfg(self):
        obs = util.datatable_cfg(
            'A Title',
            'a_name',
            'demultiplexing',
            self.cfg['rest_api'] + '/test_endpoint',
            default_sort_col='-sample_id'
        )
        exp = {
            'title': 'A Title',
            'name': 'a_name',
            'cols': col_mappings['demultiplexing'],
            'api_url': self.cfg['rest_api'] + '/test_endpoint',
            'default_sort_col': [2, 'desc'],
            'paging': True
        }
        assert obs == exp

    def test_tab_set_cfg(self):
        dt_cfg = util.datatable_cfg('Test', 'test', 'demultiplexing', self.cfg['rest_api'])
        obs = util.tab_set_cfg('A Tab Set', 'a_tab_set', [dt_cfg])
        exp = {
            'title': 'A Tab Set',
            'name': 'a_tab_set',
            'tables': [dt_cfg]
        }
        assert obs == exp
