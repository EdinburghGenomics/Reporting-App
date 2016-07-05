from tests import Helper
from config import reporting_app_config, col_mappings
from egcg_core.config import cfg
cfg.load_config_file(Helper.config_file)
from reporting_app import util


class TestBase(Helper):
    def setUp(self):
        self.cfg = reporting_app_config
        self.col_mappings = col_mappings


class TestReportingApp(TestBase):
    def test_format_order(self):
        cols = (
            {'data': 'this', 'title': 'This'},
            {'data': 'that', 'title': 'That'},
            {'data': 'other', 'title': 'Other'},
            {'data': 'another', 'title': 'Another'}
        )
        assert util._format_order('this', cols) == [0, 'asc']
        assert util._format_order('-other', cols) == [2, 'desc']

    def test_datatable_cfg(self):
        obs = util.datatable_cfg(
            'A Datatable',
            'demultiplexing',
            self.cfg['rest_api'] + '/test_endpoint',
            default_sort_col='-sample_id'
        )
        exp = {
            'title': 'A Datatable',
            'name': 'a_datatable',
            'cols': col_mappings['demultiplexing'],
            'api_url': self.cfg['rest_api'] + '/test_endpoint',
            'default_sort_col': [2, 'desc']
        }
        assert obs == exp

    def test_tab_set_cfg(self):
        dt_cfg = util.datatable_cfg('Test', 'demultiplexing', self.cfg['rest_api'])
        obs = util.tab_set_cfg('A Tab Set', [dt_cfg])
        exp = {
            'title': 'A Tab Set',
            'name': 'a_tab_set',
            'tables': [dt_cfg]
        }
        assert obs == exp
