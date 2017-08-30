from unittest.mock import patch, Mock, PropertyMock, MagicMock
from pyclarity_lims.entities import Stage, Queue, Sample, Artifact, Step
from pyclarity_lims.lims import Lims
from requests.exceptions import HTTPError
from werkzeug.exceptions import Unauthorized, Conflict
from rest_api.actions import reviews
from tests.test_rest_api import TestBase, NamedMock


_cache_samples = {}


class SideEffectWithMemory:
    def __init__(self, f):
        self.v_function = f
        self._return_values = Exception('Never Called')

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


class TestReviewInitiator(TestBase):
    initiator_cls = reviews.ReviewInitiator
    init_request = Mock(form={'review_entities': '["sample_1"]', 'username': 'user', 'password': 'pass'})
    expected_replicates = None

    def setUp(self):
        self.initiator = self.initiator_cls(self.init_request)
        self.fake_lims = MagicMock(spec=Lims, cache={})

    def tearDown(self):
        global _cache_samples
        _cache_samples = {}

    @patch('egcg_core.clarity.connection', return_value=MagicMock(spec=Lims, cache={}))
    def test_lims(self, mocked_connection):
        assert self.initiator.lims
        # Check that the Lims was found
        mocked_connection.assert_called_once_with(
            new=True, password='pass', username='user', baseuri='http://clarity.com'
        )
        self.initiator._lims = None

        mocked_connection.side_effect = HTTPError('Something broke!')
        with self.assertRaises(Unauthorized) as e:
            _ = self.initiator.lims

        assert e.exception.code == 401
        assert e.exception.description == 'Authentication in the LIMS (http://clarity.com) failed'

    @patch('egcg_core.clarity.get_list_of_samples', side_effect=SideEffectWithMemory(fake_get_list_samples))
    def test_samples_to_review(self, mocked_get_list_of_samples):
        assert self.initiator.samples_to_review[0].name == 'sample_1'

        mocked_get_list_of_samples.side_effect = HTTPError('Something else broke!')
        with self.assertRaises(Conflict) as e:
            _ = self.initiator.samples_to_review
        assert e.exception.code == 409
        assert e.exception.description == 'Some of the samples to review were not found in the LIMS. 1 samples requested 0 samples found'

    def _test_start_review(self, queue_artifacts):
        self.initiator._lims = self.fake_lims
        self.initiator._stage = Mock(spec=Stage, step=Mock())

        p_artifacts = patch.object(Queue, 'artifacts', new_callable=PropertyMock(return_value=queue_artifacts))
        p_datetime = patch.object(self.initiator_cls, 'now', return_value='some time')
        p_samples = patch.object(self.initiator_cls, 'samples_to_review', new=[create_sample('sample_1')])
        p_step = patch.object(Step, 'create', return_value=Mock(spec=Step, id='24-1234', program_names=['Upload metrics and assess samples']))
        p_replicates = patch.object(self.initiator_cls, 'artifact_replicates', return_value=self.expected_replicates)
        with p_artifacts, p_datetime, p_samples, p_step as mocked_step_create, p_replicates as mocked_replicates:
            obs = self.initiator.perform_action()
            assert obs == {
                'action_id': 'lims_24-1234',
                'started_by': 'user',
                'date_started': 'some time',
                'action_info': {
                    'lims_step_name': self.initiator.lims_step_name,
                    'lims_url': 'http://clarity.com/clarity/work-details/1234',
                    'samples': ['sample_1']
                }
            }

            mocked_step_create.assert_called_once_with(
                self.fake_lims,
                inputs=[self.initiator.samples_to_review[0].artifact],
                replicates=self.expected_replicates,
                protocol_step=self.initiator.stage.step
            )
            mocked_step_create.return_value.trigger_program.assert_called_once_with('Upload metrics and assess samples')
            mocked_replicates.assert_called_with([create_artifact('sample_1')])

    def test_start_review_queue_empty(self):
        self._test_start_review([])
        self.fake_lims.route_artifacts.assert_called_with(
            artifact_list=[create_artifact('sample_1')], stage_uri=self.initiator.stage.uri
        )

    def test_start_review_queue_not_empty(self):
        self._test_start_review([create_artifact('sample_1')])
        self.fake_lims.route_artifacts.assert_not_called()  # because everything's already in the queue


class TestRunReviewInitiator(TestReviewInitiator):
    initiator_cls = reviews.RunReviewInitiator
    expected_replicates = [8]

    @patch('rest_api.actions.reviews.db', new={'run_elements': Mock(count=Mock(return_value=8))})
    def test_artifact_replicates(self):
        self.initiator.sample_ids_to_review = ['sample_1', 'sample_2', 'sample_3']
        assert self.initiator.artifact_replicates([create_artifact('sample_1'), create_artifact('sample_2')]) == [8, 8]
