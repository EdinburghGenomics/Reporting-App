from unittest.mock import Mock

from tests import Helper
from config import rest_config, schema

class NamedMock(Mock):
    def __init__(self, realname, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = realname

class TestBase(Helper):
    def setUp(self):
        self.cfg = rest_config
        self.schema = schema
