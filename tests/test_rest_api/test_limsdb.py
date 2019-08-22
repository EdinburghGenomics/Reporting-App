from collections import defaultdict
from datetime import datetime
from unittest import TestCase
from unittest.mock import patch
from rest_api.limsdb.queries import data_models as dm
from rest_api.limsdb.queries import factories as f


def fake_sample(sample_id='X99999P001H05', species=None):
    sample = dm.Sample()
    sample.sample_name = sample_id
    sample.project_name = 'X99999'

    if species:
        sample.species = 'Homo sapiens'

    sample.add_completed_process('Receive Sample EG 6.1', datetime.strptime('01-06-15', '%d-%m-%y'), 111)
    sample.add_completed_process('Read and Eval SSQC', datetime.strptime('16-07-15', '%d-%m-%y'), 111)

    return sample

mocked_request = patch('rest_api.limsdb.queries.factories.request', return_value=fake_sample(species='Homo sapiens'))
mocked_retrieve_args = patch(
    'rest_api.limsdb.queries.factories.retrieve_args',
    return_value={'match': {'sample_id': 'X99999P001H05', 'project_id': 'X99999'}}
)

mocked_get_project_info = patch(
    'rest_api.limsdb.queries.get_project_info',
    return_value=[('X99999', datetime(2016, 9, 1, 13, 0), None, 'Jane', 'Doe', 'Number of Quoted Samples', '2')]
)

mocked_get_sample_info = patch(
    'rest_api.limsdb.queries.get_sample_info', return_value=[
        ('X99999', 'X99999P001H05', 'X99999P001', 6, 1, 'Prep Workflow', 'TruSeq PCR-Free DNA Sample Prep'),
        ('X99999', 'X99999P001H05', 'X99999P001', 6, 1, 'Species', 'Homo sapiens')
    ]
)

mocked_get_samples_and_processes = patch(
    'rest_api.limsdb.queries.get_samples_and_processes',
    return_value=[
        ('X99999', 'X99999P001H05', 'Receive Sample EG 6.1', 'COMPLETE', datetime(2016, 11, 11, 11, 45, 3, 367000), 39005),
        ('X99999', 'X99999P001H05', 'Sequencing Plate Preparation EG 2.0', 'COMPLETE', datetime(2016, 11, 23, 13, 34, 50, 491000), 39917),
        ('X99999', 'X99999P001H05', 'Create CFP Batch', 'COMPLETE', datetime(2016, 11, 24, 10, 49, 36, 980000), 39934),
        ('X99999', 'X99999P001H05', 'Read and Eval SSQC', 'COMPLETE', datetime(2016, 11, 25, 13, 56, 13, 175000), 40004)
    ]
)

mocked_get_sample_in_queues_or_progress = patch(
    'rest_api.limsdb.queries.get_sample_in_queues_or_progress', return_value=[
        ('X99999', 'X99999P001H05', 'Create PDP Pool', datetime(2016, 11, 27, 11, 14, 59, 325000), 751, None, None)
    ]
)


class TestSample(TestCase):
    def setUp(self):
        self.sample = fake_sample(species='Homo sapiens')

    def test_add_completed_process(self):

        self.sample.add_completed_process('Test Process', datetime.strptime('01-01-11', '%d-%m-%y'), 111)
        assert self.sample._processes == {('Receive Sample EG 6.1', datetime(2015, 6, 1, 0, 0), 'complete', 111),
                                          ('Read and Eval SSQC', datetime(2015, 7, 16, 0, 0), 'complete', 111),
                                          ('Test Process', datetime(2011, 1, 1, 0, 0), 'complete', 111)}

    def test_add_queue_location(self):
        self.sample.add_queue_location('Test Process', datetime.strptime('01-01-11', '%d-%m-%y'), 111)

        assert self.sample._processes == {('Receive Sample EG 6.1', datetime(2015, 6, 1, 0, 0), 'complete', 111),
                                          ('Read and Eval SSQC', datetime(2015, 7, 16, 0, 0), 'complete', 111),
                                          ('Test Process', datetime(2011, 1, 1, 0, 0), 'queued', 111)}

    def test_processes(self):
        assert self.sample.processes == [('Read and Eval SSQC', datetime(2015, 7, 16, 0, 0), 'complete', 111),
                                         ('Receive Sample EG 6.1', datetime(2015, 6, 1, 0, 0), 'complete', 111)]

    def test_all_statuses(self):
        all_statuses = self.sample.all_statuses()
        exp = [
            {
                'date': 'Jun 01 2015',
                'name': 'sample_submission',
                'processes': [{'date': 'Jun 01 2015', 'process_id': 111, 'type': 'complete', 'name': 'Receive Sample EG 6.1'}]
            },
            {
                'date': 'Jul 16 2015',
                'name': 'sample_qc',
                'processes': [
                    {'date': 'Jul 16 2015', 'process_id': 111, 'type': 'complete', 'name': 'Read and Eval SSQC'}
                ]
            }
        ]

        assert len(all_statuses) == 2
        assert all_statuses == exp

        self.sample.add_queue_location('Sequencing Plate Preparation EG 2.0', datetime.strptime('20-07-15', '%d-%m-%y'), 111)
        all_statuses = self.sample.all_statuses()
        exp.append(
            {
                'date': 'Jul 20 2015',
                'name': 'library_queue',
                'processes': [
                    {'date': 'Jul 20 2015', 'process_id': 111, 'type': 'queued', 'name': 'Sequencing Plate Preparation EG 2.0'}
                ]
            }
        )
        assert len(all_statuses) == 3
        assert all_statuses == exp

    def test_get_status_and_date(self):
        status_and_date = self.sample._get_status_and_date()
        assert status_and_date == ('sample_qc', datetime(2015, 6, 1, 0, 0))
        self.sample.add_queue_location('Sequencing Plate Preparation EG 2.0', datetime.strptime('20-07-15', '%d-%m-%y'))
        status_and_date = self.sample._get_status_and_date()
        assert status_and_date == ('library_queue', datetime(2015, 7, 20, 0, 0))

    def test_additional_status(self):
        additional_status = self.sample.additional_status
        assert additional_status == set()
        self.sample.add_completed_process('QuantStudio Data Import EG 1.0', datetime.strptime('20-07-15', '%d-%m-%y'), 111)
        additional_status = self.sample.additional_status
        assert additional_status == {'genotyped'}

    def test_library_type(self):
        library_type = self.sample.library_type
        assert library_type == 'pcr_free'

    def test_status(self):
        assert self.sample.status == 'sample_qc'

    def test_status_date(self):
        date = self.sample.status_date
        assert date == datetime(2015, 6, 1, 0, 0)

    def test_started_date(self):
        started_date = self.sample.started_date
        assert started_date == datetime(2015, 6, 1, 0, 0)
        self.sample.add_completed_process('Courier Booking EG 1.0 ST', datetime.strptime('01-01-15', '%d-%m-%y'), 111)
        started_date = self.sample.started_date
        assert started_date == datetime(2015, 6, 1, 0, 0)
        self.sample._processes.remove(('Receive Sample EG 6.1', datetime(2015, 6, 1, 0, 0), 'complete', 111))
        started_date = self.sample.started_date
        assert started_date is None

    def test_finished_date(self):
        finished_date = self.sample.finished_date
        assert finished_date is None
        self.sample.add_completed_process('Data Release EG 1.0', datetime.strptime('30-09-15', '%d-%m-%y'), 111)
        self.sample._status_and_date = None
        finished_date = self.sample.finished_date
        assert finished_date == datetime(2015, 9, 30, 0, 0)

    def test_to_json(self):
        json = self.sample.to_json()
        assert json == {
            'library_type': 'pcr_free',
            'sample_id': 'X99999P001H05',
            'species': 'Homo sapiens',
            'finished_date': None,
            'current_status': 'sample_qc',
            'started_date': '2015-06-01T00:00:00',
            'project_id': 'X99999',
            'required_yield': None,
            'required_coverage': None,
            'statuses': [
                {
                    'date': 'Jun 01 2015',
                    'name': 'sample_submission',
                    'processes': [
                        {'date': 'Jun 01 2015', 'process_id': 111, 'type': 'complete', 'name': 'Receive Sample EG 6.1'}
                    ]
                },
                {
                    'date': 'Jul 16 2015',
                    'name': 'sample_qc',
                    'processes': [
                        {'date': 'Jul 16 2015', 'process_id': 111, 'type': 'complete', 'name': 'Read and Eval SSQC'}
                    ]
                }
            ]
        }


class TestContainer(TestCase):
    def setUp(self):
        self.sample1 = fake_sample('X99999P001H05')
        self.sample2 = fake_sample('X99999P001H06')

        self.container1 = dm.Container()
        self.container1.samples = [self.sample1, self.sample2]
        self.container1.project_id = 'X99999'
        self.container1.container_name = 'X99999P001'

    def test_samples_per_status(self):
        samples_per_status, sample_per_status_date = self.container1.samples_per_status()
        assert samples_per_status == {'sample_qc': ['X99999P001H05', 'X99999P001H06']}
        self.sample1._status_and_date = self.sample2._status_and_date = None
        self.sample2.add_completed_process('Sequencing Plate Preparation EG 2.0', datetime.strptime('20-07-15', '%d-%m-%y'), 111)
        samples_per_status, sample_per_status_date  = self.container1.samples_per_status()
        assert samples_per_status == {'sample_qc': ['X99999P001H05'], 'library_queue': ['X99999P001H06']}

    def test_library_types(self):
        library_types = self.container1.library_types
        assert library_types == 'pcr_free'
        self.sample1._processes.remove(('Read and Eval SSQC', datetime(2015, 7, 16, 0, 0), 'complete', 111))
        self.sample1.add_completed_process('Amp PCR', datetime.strptime('16-07-15', '%d-%m-%y'), 111)
        library_types = self.container1.library_types
        assert set(library_types.split(', ')) == {'nano', 'pcr_free'}
        self.sample2._processes.remove(('Read and Eval SSQC', datetime(2015, 7, 16, 0, 0), 'complete', 111))
        self.sample2.add_completed_process('Amp PCR', datetime.strptime('16-07-15', '%d-%m-%y'), 111)
        library_types = self.container1.library_types
        assert library_types == 'nano'

    def test_species(self):
        self.sample1.species = 'Homo sapiens'
        self.sample2.species = 'Gallus gallus'
        species = self.container1.species
        assert set(species.split(', ')) == {'Gallus gallus', 'Homo sapiens'}
        self.sample2.species = 'Homo sapiens'
        species = self.container1.species
        assert species == 'Homo sapiens'

    def test_to_json(self):
        json = self.container1.to_json()
        assert json == {
            'library_type': 'pcr_free',
            'project_id': 'X99999',
            'plate_id': 'X99999P001',
            'sample_qc': ['X99999P001H05', 'X99999P001H06'],
            'species': '',
            'nb_samples': 2,
            'required_coverage': '',
            'required_yield': '',
            'status': {'sample_qc': {'last_modified_date': '2015-06-01T00:00:00',
                                     'samples': ['X99999P001H05', 'X99999P001H06']}}
        }


class TestProject(TestCase):
    def setUp(self):
        self.sample1 = fake_sample('X99999P001H05')
        self.sample2 = fake_sample('X99999P001H06')

        self.project = dm.Project()
        self.project.open_date = datetime(2015, 4, 1, 11, 45, 3, 367000)
        self.project.researcher_name = 'Joe Bloggs'
        self.project.udfs['Number of Quoted Samples'] = 2
        self.project.project_id = 'X99999'

    def test_to_json(self):
        json = self.project.to_json()

        assert json == {
            'project_id': 'X99999',
            'nb_samples': 0,
            'library_type': '',
            'species': '',
            'open_date': '2015-04-01T11:45:03.367000',
            'close_date': None,
            'project_status': 'open',
            'researcher_name': 'Joe Bloggs',
            'nb_quoted_samples': 2,
            'finished_date': None,
            'started_date': None,
            'required_coverage': '',
            'required_yield': '',
            'status': defaultdict(set)
        }

        self.sample1.species = 'Homo sapiens'
        self.sample2.species = 'Homo sapiens'
        self.project.samples = [self.sample1, self.sample2]
        self.sample1.add_completed_process('Finish Processing EG 1.0 ST', datetime.strptime('01-09-15', '%d-%m-%y'), 111)
        self.sample2.add_completed_process('Finish Processing EG 1.0 ST', datetime.strptime('01-09-15', '%d-%m-%y'), 111)

        json = self.project.to_json()
        assert json == {
            'project_id': 'X99999',
            'nb_samples': 2,
            'library_type': 'pcr_free',
            'species': 'Homo sapiens',
            'open_date': '2015-04-01T11:45:03.367000',
            'close_date': None,
            'project_status': 'open',
            'researcher_name': 'Joe Bloggs',
            'nb_quoted_samples': 2,
            'finished_date': '2015-09-01T00:00:00',
            'started_date': '2015-06-01T00:00:00',
            'finished': ['X99999P001H05', 'X99999P001H06'],
            'required_coverage': '',
            'required_yield': '',
            'status': {'finished': {'last_modified_date': '2015-09-01T00:00:00', 'samples': ['X99999P001H05', 'X99999P001H06']}}
        }

    def test_finished_date(self):
        self.project.samples = [self.sample1, self.sample2]
        finished_date = self.project.finished_date
        assert finished_date is None
        for sample in [self.sample1, self.sample2]:
            sample._status_and_date = None
            sample.add_completed_process('Finish Processing EG 1.0 ST', datetime.strptime('01-09-15', '%d-%m-%y'), 111)
        finished_date = self.project.finished_date
        assert finished_date == datetime(2015, 9, 1, 0, 0)

    def test_started_date(self):
        started_date = self.project.started_date
        assert started_date is None
        self.project.samples = [self.sample1, self.sample2]
        started_date = self.project.started_date
        assert started_date == datetime(2015, 6, 1, 0, 0)


@mocked_get_sample_info
@mocked_get_samples_and_processes
@mocked_get_sample_in_queues_or_progress
@mocked_request
def test_create_samples(mocked_request, mocked_non_qc, mocked_samples_processes, mocked_sample_info):
    created_samples = f._create_samples(None, match={'sample_id': 'X99999P001H05'})
    c = list(created_samples)[0]
    assert c._processes == {
        ('Create PDP Pool', datetime(2016, 11, 27, 11, 14, 59, 325000), 'queued', 751),
        ('Receive Sample EG 6.1', datetime(2016, 11, 11, 11, 45, 3, 367000), 'complete', 39005),
        ('Sequencing Plate Preparation EG 2.0', datetime(2016, 11, 23, 13, 34, 50, 491000), 'complete', 39917),
        ('Create CFP Batch', datetime(2016, 11, 24, 10, 49, 36, 980000), 'complete', 39934),
        ('Read and Eval SSQC', datetime(2016, 11, 25, 13, 56, 13, 175000), 'complete', 40004)
    }
    assert c.original_name == c.sample_name == 'X99999P001H05'
    assert c.planned_library == 'TruSeq PCR-Free DNA Sample Prep'
    assert c.plate_name == 'X99999P001'
    assert c.project_name == 'X99999'
    assert c.species == 'Homo sapiens'
    assert c.started_date == datetime(2016, 11, 11, 11, 45, 3, 367000)
    assert c.status == 'sequencing_queue'
    assert c.status_date == datetime(2016, 11, 27, 11, 14, 59, 325000)


@mocked_get_sample_info
@mocked_get_samples_and_processes
@mocked_get_sample_in_queues_or_progress
@mocked_request
@mocked_retrieve_args
def test_sample_status(mock_retrieve_args, mocked_request, mocked_non_qc, mocked_samples_processes, mocked_sample_info):
    session = None
    s = f.sample_status(session)
    assert s == [
        {
            'started_date': '2016-11-11T11:45:03.367000',
            'species': 'Homo sapiens',
            'current_status': 'sequencing_queue',
            'project_id': 'X99999',
            'library_type': 'pcr_free',
            'finished_date': None,
            'sample_id': 'X99999P001H05',
            'required_coverage': None,
            'required_yield': None,
            'statuses': [
                {'processes': [{'name': 'Receive Sample EG 6.1', 'type': 'complete', 'date': 'Nov 11 2016', 'process_id': 39005}], 'name': 'sample_submission', 'date': 'Nov 11 2016'},
                {'processes': [{'name': 'Sequencing Plate Preparation EG 2.0', 'type': 'complete', 'date': 'Nov 23 2016', 'process_id': 39917}], 'name': 'sample_qc', 'date': 'Nov 23 2016'},
                {'processes': [{'name': 'Create CFP Batch', 'type': 'complete', 'date': 'Nov 24 2016', 'process_id': 39934}], 'name': 'library_queue', 'date': 'Nov 24 2016'},
                {'processes': [{'name': 'Read and Eval SSQC', 'type': 'complete', 'date': 'Nov 25 2016', 'process_id': 40004}], 'name': 'library_preparation', 'date': 'Nov 25 2016'},
                {'processes': [{'name': 'Create PDP Pool', 'type': 'queued', 'date': 'Nov 27 2016', 'process_id': 751}], 'name': 'sequencing_queue', 'date': 'Nov 27 2016'}
            ]
        }
    ]


@mocked_get_sample_info
@mocked_get_samples_and_processes
@mocked_get_sample_in_queues_or_progress
@mocked_request
@mocked_get_project_info
@mocked_retrieve_args
def test_sample_status_per_project(m_retrieve_args, m_project_info, m_request, m_non_qc, m_processes, m_sample_info):
    session = None
    s = f.sample_status_per_project(session)
    assert s == [
        {
            'researcher_name': 'Jane Doe',
            'sequencing_queue': ['X99999P001H05'],
            'open_date': '2016-09-01T13:00:00',
            'close_date': None,
            'project_status': 'open',
            'finished_date': None,
            'nb_quoted_samples': '2',
            'started_date': '2016-11-11T11:45:03.367000',
            'library_type': 'pcr_free',
            'nb_samples': 1,
            'species': 'Homo sapiens',
            'project_id': 'X99999',
            'required_coverage': '',
            'required_yield': '',
            'status': {'sequencing_queue': {'samples': ['X99999P001H05'], 'last_modified_date': '2016-11-27T11:14:59.325000'}}
        }
    ]


@mocked_get_sample_info
@mocked_get_samples_and_processes
@mocked_get_sample_in_queues_or_progress
@mocked_request
@mocked_get_project_info
@mocked_retrieve_args
def test_sample_status_per_plate(m_retrieve_args, m_project_info, m_request, m_non_qc, m_processes, m_sample_info):
    session = None
    s = f.sample_status_per_plate(session)
    assert s == [
        {
            'nb_samples': 1,
            'sequencing_queue': ['X99999P001H05'],
            'library_type': 'pcr_free',
            'plate_id': 'X99999P001',
            'species': 'Homo sapiens',
            'project_id': 'X99999',
            'required_coverage': '',
            'required_yield': '',
            'status': {'sequencing_queue': {'samples': ['X99999P001H05'], 'last_modified_date': '2016-11-27T11:14:59.325000'}}
        }
    ]


@mocked_retrieve_args
@patch('rest_api.limsdb.queries.step_info')
def test_library_preparation(mocked_library_info, mocked_retrieve_args):
    mocked_library_info.return_value = (
        ('qpcr1', datetime(2019, 5, 2), 'lib1', 'TruSeq Nano Sample Prep', 1, 'a_mod_date', 'sample_1', 'a_project', 0, 0, 'a_udf', 1.0, 'sample_udf', 'A'),
        ('qpcr1', datetime(2019, 5, 2), 'lib1', 'TruSeq Nano Sample Prep', 1, 'a_mod_date', 'sample_1', 'a_project', 0, 0, 'another_udf', 2.1, 'sample_udf', 'A'),
        ('qpcr1', datetime(2019, 5, 2), 'lib1', 'TruSeq PCR-Free Sample Prep', 1, 'a_mod_date', 'sample_2', 'a_project', 1, 0, 'a_udf', 3.2, 'sample_udf', 'A'),
        ('qpcr2', datetime(2019, 5, 1), 'lib1', 'TruSeq Nano Sample Prep', 1, 'a_mod_date', 'sample_1', 'a_project', 0, 0, 'a_udf', 1.4, 'sample_udf', 'A')
    )
    assert f.library_info(None) == [
        {
            'id': 'lib1',
            'step_link': 'http://clarity.com/clarity/work-complete/qpcr1',
            'step_run': 2,
            'date_completed': '2019-05-02T00:00:00',
            'samples': [
                {
                    'name': 'sample_1',
                    'location': 'A:1',
                    'udfs': {'a_udf': 1.0, 'sample_udf': 'A', 'another_udf': 2.1},
                    'qc_flag': 'PASSED',
                    'project_id': 'a_project'
                },
                {
                    'name': 'sample_2',
                    'location': 'A:2',
                    'udfs': {'a_udf': 3.2, 'sample_udf': 'A'},
                    'qc_flag': 'PASSED',
                    'project_id': 'a_project'
                }
            ],
            'protocol': 'nano',
            'nsamples': 2,
            'pc_qc_flag_pass': 100.0,
            'project_ids': ['a_project']
        }
    ]
