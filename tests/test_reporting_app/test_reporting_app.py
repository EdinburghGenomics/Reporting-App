from unittest.mock import patch
from tests import Helper
from config import reporting_app_config as cfg, col_mappings
from reporting_app import util


class FakeUser:
    login_token = 'an_api_token'


class FakeRequest:
    cookies = {'remember_token': 'a_token'}


class TestReportingApp(Helper):
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
        with patch('reporting_app.util.request', new=FakeRequest):
            obs = util.datatable_cfg(
                'A Datatable',
                'demultiplexing',
                cfg['rest_api'] + '/test_endpoint',
                default_sort_col='-sample_id'
            )
        exp = {
            'title': 'A Datatable',
            'name': 'a_datatable',
            'cols': col_mappings['demultiplexing'],
            'api_url': cfg['rest_api'] + '/test_endpoint',
            'default_sort_col': [2, 'desc'],
            'token': util.encode_string('a_token')
        }
        assert obs == exp

    def test_tab_set_cfg(self):

        with patch('reporting_app.util.request', new=FakeRequest):
            dt_cfg = util.datatable_cfg('Test', 'demultiplexing', cfg['rest_api'])
        obs = util.tab_set_cfg('A Tab Set', [dt_cfg])
        exp = {
            'title': 'A Tab Set',
            'name': 'a_tab_set',
            'tables': [dt_cfg]
        }
        assert obs == exp
