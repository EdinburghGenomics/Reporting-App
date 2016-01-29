from tests import Helper
from config import rest_config, schema


class TestBase(Helper):
    def setUp(self):
        self.cfg = rest_config
        self.schema = schema
