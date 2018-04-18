import os
import unittest
from time import sleep
from unittest.mock import patch

from config import rest_config as cfg

from rest_api import app
from tests.test_rest_api import TestBase


class TestRestAPI(TestBase):

    @classmethod
    def setUpClass(cls):
        app.testing = True
        cls.client = app.test_client()

        sleep(1)

        cls.patched_auth = patch('auth.DualAuth.authorized', return_value=True)
        cls.patched_auth.start()
        del cfg.content['lims_database']

    def test_lims_endpoints(self):
        # only test that the enpoints exists
        # Additional test would require adding to the in memory sqlite database
        for endpoint in ['project_status', 'plate_status', 'sample_status', 'run_status', 'sample_info', 'project_info']:
            response = self.client.get('/api/0.1/lims/' + endpoint)
            assert response.status_code == 200
