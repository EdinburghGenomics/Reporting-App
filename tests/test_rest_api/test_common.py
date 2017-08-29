from unittest.mock import patch, PropertyMock
import datetime
from rest_api.common import convert_date
from tests import Helper


class TestCommon(Helper):
    def test_convert_date(self):
        with patch('rest_api.common.app', return_value=PropertyMock()) as patch_app:
            patch_app.config = {'DATE_FORMAT': '%d_%m_%Y_%H:%M:%S'}
            date_str = '10_04_2017_14:39:00'
            date = datetime.datetime.strptime(date_str, '%d_%m_%Y_%H:%M:%S')
            assert convert_date('test') == 'test'
            assert convert_date(['test']) == ['test']
            assert convert_date({'key': 'test'}) == {'key': 'test'}
            assert convert_date(date_str) == date
            assert convert_date({'key': 'test', 'date': date_str}) == {'key': 'test', 'date': date}
