from unittest.case import TestCase

from datetime import datetime

from rest_api.limsdb.queries.project_status import Sample
from tests.test_rest_api.test_aggregation import TestAggregation, FakeRequest
from unittest.mock import Mock, patch
from rest_api.aggregation import database_side
from rest_api.aggregation.database_side import stages as s


class SampleTest(TestCase):

    def setUp(self):
        self.sample = Sample()
        self.sample.add_completed_process('Receive Sample EG 6.1', datetime.strptime('01-06-15', '%d-%m-%y'))
        self.sample.add_completed_process('Read and Eval SSQC', datetime.strptime('16-07-15', '%d-%m-%y'))

    def tearDown(self):
        pass

    def test_status(self):
        assert self.sample.status == 'sample_qc'
