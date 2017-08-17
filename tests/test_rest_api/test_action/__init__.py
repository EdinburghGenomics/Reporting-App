from unittest.mock import patch, Mock, PropertyMock, MagicMock

from pyclarity_lims.entities import Stage, Queue, ProtocolStep, Sample, Artifact
from pyclarity_lims.lims import Lims

from rest_api.actions import start_run_review
from rest_api import app as current_app
from tests.test_rest_api import TestBase, NamedMock

def create_sample(name):
    s = NamedMock(spec=Sample, realname=name)
    s.artifact = Mock(spec=Artifact, samples=[s])
    return s

def fake_get_list_samples(sample_names):
    return [create_sample(n) for n in sample_names]

class TestAction(TestBase):

    @patch('egcg_core.clarity.connection', return_value=MagicMock(spec=Lims, cache={}))
    @patch('egcg_core.clarity.get_workflow_stage', return_value=Mock(spec=Stage, step=Mock(spec=ProtocolStep, permittedcontainers=[])))
    @patch.object(Queue,'artifacts', return_value=PropertyMock)
    @patch('egcg_core.clarity.get_list_of_samples', side_effect=fake_get_list_samples)
    def test_run_review(self, mocked_get_samples, mocked_queue_artifacts, mocked_stage, mocked_connection):
        with current_app.test_request_context(method='POST', query_string='samples=["sample1"]&username="user"&password="pass"'):
            start_run_review()

