import pprint
from unittest.mock import patch, Mock, PropertyMock, MagicMock

from pyclarity_lims.entities import Stage, Queue, ProtocolStep, Sample, Artifact, Step
from pyclarity_lims.lims import Lims

from rest_api.actions import start_run_review
from tests.test_rest_api import TestBase, NamedMock


_cache_samples = {}

class SideEffectWithMemory():
    def __init__(self, f):
        self.v_function = f
        self._return_values = Exception("Never Called")

    def __call__(self, *args, **kwargs):
        try:
            self._return_value = self.v_function(*args, **kwargs)
            return self._return_value
        except Exception as e:
            self._return_value = e
            raise e

    @property
    def return_value(self):
        if isinstance(self._return_value, Exception):
            raise self._return_value
        return self._return_value


def create_sample(name):
    global _cache_samples
    if name not in _cache_samples:
        s = NamedMock(spec=Sample, realname=name)
        s.artifact = Mock(spec=Artifact, samples=[s])
        _cache_samples[name] = s
    return _cache_samples.get(name)


def create_artifact(name):
    s = create_sample(name)
    return s.artifact


def fake_get_list_samples(sample_names):
    return [create_sample(n) for n in sample_names]

class TestRunReview(TestBase):

    def setUp(self):
        self.patch_connection = patch('egcg_core.clarity.connection', return_value=MagicMock(spec=Lims, cache={}))
        self.patch_workflow_stage = patch('egcg_core.clarity.get_workflow_stage', return_value=Mock(spec=Stage, step=Mock()))
        self.patch_queue_empty = patch.object(Queue, 'artifacts', new_callable=PropertyMock(return_value=[]))
        self.patch_queue_sample = patch.object(Queue, 'artifacts', new_callable=PropertyMock(return_value=[create_artifact('sample1')]))
        self.patch_list_of_samples = patch('egcg_core.clarity.get_list_of_samples', side_effect=SideEffectWithMemory(fake_get_list_samples))
        self.patch_step_create = patch.object(Step, 'create', return_value=Mock(spec=Step, id='24-1234', program_names=['prog1']))
        self.patch_count_re1 = patch('rest_api.actions.reviews.count_run_element', return_value=1)

    def tearDown(self):
        global _cache_samples
        _cache_samples = {}

    def test_run_review1(self):

        with self.patch_connection as mocked_connection, self.patch_workflow_stage as mocked_stage, \
             self.patch_queue_empty as mocked_queue_artifacts, self.patch_list_of_samples as mocked_get_samples, \
             self.patch_step_create as mocked_step_create, self.patch_count_re1:

            start_run_review(Mock(form={'samples':'["sample1"]','username': 'user', 'password': 'pass'}))
            #Check that the Lims was found
            mocked_connection.assert_called_once_with(new=True, password='pass', username='user', baseuri='http://clarity.com')
            # Check that the stage was found
            mocked_stage.assert_called_once_with(workflow_name='PostSeqLab EG 1.0 WF',
                                                 stage_name='Sequencer Output Review EG 1.0 ST')
            # Check that the sample was found
            mocked_get_samples.assert_called_once_with(sample_names=['sample1'])
            #Check that the step was created
            mocked_step_create.assert_called_once_with(
                mocked_connection.return_value,
                inputs=[mocked_get_samples.side_effect.return_value[0].artifact],
                replicates=[1],
                protocol_step=mocked_stage.return_value.step
            )
            assert mocked_queue_artifacts == []

    def test_run_review2(self):

        with self.patch_connection as mocked_connection, self.patch_workflow_stage as mocked_stage, \
                self.patch_queue_sample as mocked_queue_artifacts, self.patch_list_of_samples as mocked_get_samples, \
                self.patch_step_create as mocked_step_create, self.patch_count_re1:

            start_run_review(Mock(form={'samples':'["sample1"]','username': 'user', 'password': 'pass'}))

            #Check that the Lims was found
            mocked_connection.assert_called_once_with(new=True, password='pass', username='user', baseuri='http://clarity.com')
            # Check that the stage was found
            mocked_stage.assert_called_once_with(workflow_name='PostSeqLab EG 1.0 WF',
                                                 stage_name='Sequencer Output Review EG 1.0 ST')
            # Check that the sample was found
            mocked_get_samples.assert_called_once_with(sample_names=['sample1'])
            #Check that the step was created
            mocked_step_create.assert_called_once_with(
                mocked_connection.return_value,
                inputs=[mocked_queue_artifacts[0]],
                replicates=[1],
                protocol_step=mocked_stage.return_value.step
            )
            mocked_queue_artifacts



