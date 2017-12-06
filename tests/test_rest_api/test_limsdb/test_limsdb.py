from unittest.case import TestCase
from datetime import datetime
from rest_api.limsdb.queries.sample_status import Sample, Container, Project, _create_samples, sample_status, sample_status_per_project, sample_status_per_plate
from unittest.mock import patch

mocked_sample = Sample()
mocked_sample.sample_name = 'X99999P001H05'
mocked_sample.project_name = 'X99999'
mocked_sample.species = 'Homo sapiens'
mocked_sample.add_completed_process('Receive Sample EG 6.1', datetime.strptime('01-06-15', '%d-%m-%y'))
mocked_sample.add_completed_process('Read and Eval SSQC', datetime.strptime('16-07-15', '%d-%m-%y'))

mocked_request = patch('rest_api.limsdb.queries.sample_status.request', return_value=mocked_sample)
mocked_retrieve_args = patch('rest_api.limsdb.queries.sample_status.retrieve_args', return_value={'match': {'sample_id': 'X99999P001H05', 'project_id': 'X99999'}})
mocked_get_project_info = patch('rest_api.limsdb.queries.get_project_info', return_value=[('X99999', datetime(2016, 9, 1, 13, 0), 'Jane', 'Doe', 'Number of Quoted Samples', '2')])

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

mocked_non_QC_queues = patch(
    'rest_api.limsdb.queries.non_QC_queues', return_value=[
        ('X99999', 'X99999P001H05', 'Create PDP Pool', datetime(2016, 11, 27, 11, 14, 59, 325000), 751)
    ]
)


class SampleTest(TestCase):

    def setUp(self):
        self.sample1 = Sample()
        self.sample1.sample_name = 'test_sample'
        self.sample1.project_name = 'test_project'
        self.sample1.species = 'Homo sapiens'
        self.sample1.add_completed_process('Receive Sample EG 6.1', datetime.strptime('01-06-15', '%d-%m-%y'))
        self.sample1.add_completed_process('Read and Eval SSQC', datetime.strptime('16-07-15', '%d-%m-%y'))

    def tearDown(self):
        pass

    def test_add_completed_process(self):

        self.sample1.add_completed_process('Test Process', datetime.strptime('01-01-11', '%d-%m-%y'))
        assert self.sample1._processes == {('Receive Sample EG 6.1', datetime(2015, 6, 1, 0, 0), 'complete', None),
                                           ('Read and Eval SSQC', datetime(2015, 7, 16, 0, 0), 'complete', None),
                                           ('Test Process', datetime(2011, 1, 1, 0, 0), 'complete', None)}

    def test_add_queue_location(self):
        self.sample1.add_queue_location('Test Process', datetime.strptime('01-01-11', '%d-%m-%y'))

        assert self.sample1._processes == {('Receive Sample EG 6.1', datetime(2015, 6, 1, 0, 0), 'complete', None),
                                           ('Read and Eval SSQC', datetime(2015, 7, 16, 0, 0), 'complete', None),
                                           ('Test Process', datetime(2011, 1, 1, 0, 0), 'queued', None)}


    def test_processes(self):
        assert self.sample1.processes ==[('Read and Eval SSQC', datetime(2015, 7, 16, 0, 0), 'complete', None),
                                         ('Receive Sample EG 6.1', datetime(2015, 6, 1, 0, 0), 'complete', None)]

    def test_all_statuses(self):
        all_status = self.sample1.all_statuses()
        assert len(all_status) == 2
        assert all_status == \
               [
                      {'date': 'Jun 01 2015',
                       'processes':
                           [
                               {'date': 'Jun 01 2015',
                                'process_id': None,
                                'type': 'complete',
                                'name': 'Receive Sample EG 6.1'}
                           ],
                       'name': 'sample_submission'},
                      {'date': 'Jul 16 2015',
                       'processes':
                           [
                               {'date': 'Jul 16 2015',
                                'process_id': None,
                                'type': 'complete',
                                'name': 'Read and Eval SSQC'}
                           ],
                       'name': 'sample_qc'},
               ]

        self.sample1.add_queue_location('Sequencing Plate Preparation EG 2.0', datetime.strptime('20-07-15', '%d-%m-%y'))
        all_status = self.sample1.all_statuses()
        assert len(all_status) == 3
        assert all_status == \
               [
                      {'date': 'Jun 01 2015',
                       'processes':
                           [
                               {'date': 'Jun 01 2015',
                            'process_id': None,
                                'type': 'complete',
                                'name': 'Receive Sample EG 6.1'}
                           ],
                       'name': 'sample_submission'},
                      {'date': 'Jul 16 2015',
                       'processes':
                           [
                               {'date': 'Jul 16 2015',
                                'process_id': None,
                                'type': 'complete',
                                'name': 'Read and Eval SSQC'}
                           ],
                       'name': 'sample_qc'},
                      {'date': 'Jul 20 2015',
                       'processes':
                           [
                               {'date': 'Jul 20 2015',
                                'process_id': None,
                                'type': 'queued',
                                'name': 'Sequencing Plate Preparation EG 2.0'}
                           ],
                       'name': 'library_queue'}
               ]

    def test_get_status_and_date(self):
        status_and_date = self.sample1._get_status_and_date()
        assert status_and_date == ('sample_qc', datetime(2015, 6, 1, 0, 0))
        self.sample1.add_queue_location('Sequencing Plate Preparation EG 2.0', datetime.strptime('20-07-15', '%d-%m-%y'))
        status_and_date = self.sample1._get_status_and_date()
        assert status_and_date == ('library_queue', datetime(2015, 7, 20, 0, 0))

    def test_additional_status(self):
        additional_status = self.sample1.additional_status
        assert additional_status == set()
        self.sample1.add_completed_process('QuantStudio Data Import EG 1.0', datetime.strptime('20-07-15', '%d-%m-%y'))
        additional_status = self.sample1.additional_status
        assert additional_status == {'genotyped'}

    def test_library_type(self):
        library_type = self.sample1.library_type
        assert library_type == 'pcr_free'

    def test_status(self):
        assert self.sample1.status == 'sample_qc'

    def test_status_date(self):
        date = self.sample1.status_date
        assert date == datetime(2015, 6, 1, 0, 0)

    def test_started_date(self):
        started_date = self.sample1.started_date
        assert started_date == datetime(2015, 6, 1, 0, 0)
        self.sample1.add_completed_process('Courier Booking EG 1.0 ST', datetime.strptime('01-01-15', '%d-%m-%y'))
        started_date = self.sample1.started_date
        assert started_date == datetime(2015, 6, 1, 0, 0)
        self.sample1._processes.remove(('Receive Sample EG 6.1', datetime(2015, 6, 1, 0, 0), 'complete', None))
        started_date = self.sample1.started_date
        assert started_date is None

    def test_finished_date(self):
        finished_date = self.sample1.finished_date
        assert finished_date is None
        self.sample1.add_completed_process('Data Release EG 1.0', datetime.strptime('30-09-15', '%d-%m-%y'))
        self.sample1._status_and_date = None
        finished_date = self.sample1.finished_date
        assert finished_date == datetime(2015, 9, 30, 0, 0)

    def test_to_json(self):
        json = self.sample1.to_json()
        assert json == {'library_type': 'pcr_free',
                     'sample_id': 'test_sample',
                     'species': 'Homo sapiens',
                     'finished_date': None,
                     'current_status': 'sample_qc',
                     'started_date': '2015-06-01T00:00:00',
                     'statuses': [
                         {'date': 'Jun 01 2015',
                          'processes':
                              [
                                  {'date': 'Jun 01 2015',
                                   'process_id': None,
                                   'type': 'complete',
                                   'name': 'Receive Sample EG 6.1'}
                              ],
                          'name': 'sample_submission'},
                         {'date': 'Jul 16 2015',
                          'processes':
                              [
                                  {'date': 'Jul 16 2015',
                                   'process_id': None,
                                   'type': 'complete',
                                   'name': 'Read and Eval SSQC'}
                          ],
                          'name': 'sample_qc'}
                     ],
                     'project_id': 'test_project'}


class ContainerTest(TestCase):

    def setUp(self):
        self.container1 = Container()

        self.sample1 = Sample()
        self.sample1.sample_name = 'test_sample1'
        self.sample1.project_name = 'test_project1'
        self.sample1.add_completed_process('Receive Sample EG 6.1', datetime.strptime('01-06-15', '%d-%m-%y'))
        self.sample1.add_completed_process('Read and Eval SSQC', datetime.strptime('16-07-15', '%d-%m-%y'))

        self.sample2 = Sample()
        self.sample2.sample_name = 'test_sample2'
        self.sample2.project_name = 'test_project1'
        self.sample2.add_completed_process('Receive Sample EG 6.1', datetime.strptime('01-06-15', '%d-%m-%y'))
        self.sample2.add_completed_process('Read and Eval SSQC', datetime.strptime('16-07-15', '%d-%m-%y'))

        self.container1.samples = [self.sample1, self.sample2]
        self.container1.project_id = 'test_project'
        self.container1.name = 'test_plate1'

    def tearDown(self):
        pass

    def test_samples_per_status(self):
        samples_per_status = self.container1.samples_per_status()
        assert samples_per_status == {'sample_qc': ['test_sample1', 'test_sample2']}
        self.sample1._status_and_date = self.sample2._status_and_date = None
        self.sample2.add_completed_process('Sequencing Plate Preparation EG 2.0', datetime.strptime('20-07-15', '%d-%m-%y'))
        samples_per_status = self.container1.samples_per_status()
        assert samples_per_status == {'sample_qc': ['test_sample1'], 'library_queue': ['test_sample2']}

    def test_library_types(self):
        library_types = self.container1.library_types
        assert library_types == 'pcr_free'
        self.sample1._processes.remove(('Read and Eval SSQC', datetime(2015, 7, 16, 0, 0), 'complete', None))
        self.sample1.add_completed_process('Amp PCR', datetime.strptime('16-07-15', '%d-%m-%y'))
        library_types = self.container1.library_types
        assert set(library_types.split(', ')) == set(['nano', 'pcr_free'])
        self.sample2._processes.remove(('Read and Eval SSQC', datetime(2015, 7, 16, 0, 0), 'complete', None))
        self.sample2.add_completed_process('Amp PCR', datetime.strptime('16-07-15', '%d-%m-%y'))
        library_types = self.container1.library_types
        assert library_types == 'nano'
        for sample in [self.sample1, self.sample2]:
            sample._processes.remove(('Amp PCR', datetime(2015, 7, 16, 0, 0), 'complete', None))
            sample.add_completed_process('Read and Eval SSQC', datetime.strptime('16-07-15', '%d-%m-%y'))

    def test_species(self):
        self.sample1.species = 'Homo sapiens'
        self.sample2.species = 'Gallus gallus'
        species = self.container1.species
        assert set(species.split(', ')) == set(['Gallus gallus', 'Homo sapiens'])
        self.sample2.species = 'Homo sapiens'
        species = self.container1.species
        assert species == 'Homo sapiens'

    def test_to_json(self):
        json = self.container1.to_json()
        assert json == {
                        'library_type': 'pcr_free',
                        'project_id': 'test_project',
                        'plate_id': 'test_plate1',
                        'sample_qc': ['test_sample1', 'test_sample2'],
                        'species': '', 'nb_samples': 2
                        }


class ProjectTest(TestCase):

    def setUp(self):
        self.sample1 = Sample()
        self.sample1.sample_name = 'test_sample1'
        self.sample1.project_name = 'test_project1'
        self.sample1.add_completed_process('Receive Sample EG 6.1', datetime.strptime('01-06-15', '%d-%m-%y'), process_id=10)
        self.sample1.add_completed_process('Read and Eval SSQC', datetime.strptime('16-07-15', '%d-%m-%y'), process_id=11)

        self.sample2 = Sample()
        self.sample2.sample_name = 'test_sample2'
        self.sample2.project_name = 'test_project1'
        self.sample2.add_completed_process('Receive Sample EG 6.1', datetime.strptime('01-06-15', '%d-%m-%y'), process_id=12)
        self.sample2.add_completed_process('Read and Eval SSQC', datetime.strptime('16-07-15', '%d-%m-%y'), process_id=13)

        self.project1 = Project()
        self.project1.open_date = datetime(2015, 4, 1, 11, 45, 3, 367000)
        self.project1.researcher_name = 'Joe Bloggs'
        self.project1.nb_quoted_samples = 2

        self.project1.project_id = 'test_project'
        self.project1.name = 'test_plate1'

    def tearDown(self):
        pass

    def test_to_json(self):
        json = self.project1.to_json()
        assert json ==  {
            'project_id': 'test_plate1',
            'nb_samples': 0,
            'library_type': '',
            'species': '',
            'open_date': '2015-04-01T11:45:03.367000',
            'researcher_name': 'Joe Bloggs',
            'nb_quoted_samples': 2,
            'finished_date': None,
            'started_date': None
        }

        self.sample1.species = 'Homo sapiens'
        self.sample2.species = 'Homo sapiens'
        self.project1.samples = [self.sample1, self.sample2]
        self.sample1.add_completed_process('Finish Processing EG 1.0 ST', datetime.strptime('01-09-15', '%d-%m-%y'), process_id=14)
        self.sample2.add_completed_process('Finish Processing EG 1.0 ST', datetime.strptime('01-09-15', '%d-%m-%y'), process_id=15)

        json = self.project1.to_json()
        assert json == {
            'project_id': 'test_plate1',
            'nb_samples': 2,
            'library_type': 'pcr_free',
            'species': 'Homo sapiens',
            'open_date': '2015-04-01T11:45:03.367000',
            'researcher_name': 'Joe Bloggs',
            'nb_quoted_samples': 2,
            'finished_date': '2015-09-01T00:00:00',
            'started_date': '2015-06-01T00:00:00',
            'finished': ['test_sample1', 'test_sample2']
        }

    def test_finished_date(self):
        self.project1.samples = [self.sample1, self.sample2]
        finished_date = self.project1.finished_date
        assert finished_date is None
        for sample in [self.sample1, self.sample2]:
            sample._status_and_date = None
            sample.add_completed_process('Finish Processing EG 1.0 ST', datetime.strptime('01-09-15', '%d-%m-%y'), process_id=16)
        finished_date = self.project1.finished_date
        assert finished_date == datetime(2015, 9, 1, 0, 0)

    def test_started_date(self):
        started_date = self.project1.started_date
        assert started_date is None
        self.project1.samples = [self.sample1, self.sample2]
        started_date = self.project1.started_date
        assert started_date == datetime(2015, 6, 1, 0, 0)

@mocked_get_sample_info
@mocked_get_samples_and_processes
@mocked_non_QC_queues
@mocked_request
def test_create_samples(mocked_request,
                        mocked_non_qc,
                        mocked_samples_processes,
                        mocked_sample_info):
    match = {'sample_id': 'X99999P001H05'}
    session = None
    created_samples = _create_samples(session, match)
    c = list(created_samples)[0]
    assert c._processes == {
                            ('Create PDP Pool', datetime(2016, 11, 27, 11, 14, 59, 325000), 'queued', 751),
                            ('Receive Sample EG 6.1', datetime(2016, 11, 11, 11, 45, 3, 367000), 'complete', 39005),
                            ('Sequencing Plate Preparation EG 2.0', datetime(2016, 11, 23, 13, 34, 50, 491000), 'complete', 39917),
                            ('Create CFP Batch', datetime(2016, 11, 24, 10, 49, 36, 980000), 'complete', 39934),
                            ('Read and Eval SSQC', datetime(2016, 11, 25, 13, 56, 13, 175000), 'complete', 40004)
                            }
    assert c.original_name == 'X99999P001H05'
    assert c.planned_library == 'TruSeq PCR-Free DNA Sample Prep'
    assert c.plate_name == 'X99999P001'
    assert c.project_name == 'X99999'
    assert c.sample_name == 'X99999P001H05'
    assert c.species == 'Homo sapiens'
    assert c.started_date == datetime(2016, 11, 11, 11, 45, 3, 367000)
    assert c.status == 'sequencing_queue'
    assert c.status_date == datetime(2016, 11, 27, 11, 14, 59, 325000)


@mocked_get_sample_info
@mocked_get_samples_and_processes
@mocked_non_QC_queues
@mocked_request
@mocked_retrieve_args
def test_sample_status(mock_retrieve_args,
                       mocked_request,
                       mocked_non_qc,
                       mocked_samples_processes,
                       mocked_sample_info):
    session = None
    s = sample_status(session)
    assert s == [
        {
            'started_date': '2016-11-11T11:45:03.367000', 'species': 'Homo sapiens', 'current_status': 'sequencing_queue', 'project_id': 'X99999',
            'statuses': [
                {'processes':
                    [
                    {'name': 'Receive Sample EG 6.1', 'type': 'complete', 'date': 'Nov 11 2016', 'process_id': 39005}
                    ], 'name': 'sample_submission', 'date': 'Nov 11 2016'},
                {'processes':
                    [
                    {'name': 'Sequencing Plate Preparation EG 2.0', 'type': 'complete', 'date': 'Nov 23 2016', 'process_id': 39917}
                    ], 'name': 'sample_qc', 'date': 'Nov 23 2016'},
                {'processes':
                    [
                    {'name': 'Create CFP Batch', 'type': 'complete', 'date': 'Nov 24 2016', 'process_id': 39934}
                    ], 'name': 'library_queue', 'date': 'Nov 24 2016'},
                {'processes':
                    [
                    {'name': 'Read and Eval SSQC', 'type': 'complete', 'date': 'Nov 25 2016', 'process_id': 40004}
                    ], 'name': 'library_preparation', 'date': 'Nov 25 2016'},
                {'processes':
                    [
                    {'name': 'Create PDP Pool', 'type': 'queued', 'date': 'Nov 27 2016', 'process_id': 751}
                    ], 'name': 'sequencing_queue', 'date': 'Nov 27 2016'}],
            'library_type': 'pcr_free', 'finished_date': None, 'sample_id': 'X99999P001H05'
        }
    ]

@mocked_get_sample_info
@mocked_get_samples_and_processes
@mocked_non_QC_queues
@mocked_request
@mocked_get_project_info
@mocked_retrieve_args
def test_sample_status_per_project(mocked_retrieve_args,
                                   mocked_project_info,
                                   mocked_request,
                                   mocked_non_qc,
                                   mocked_samples_processes,
                                   mocked_sample_info):
    session = None
    s = sample_status_per_project(session)
    assert s == [
        {
            'researcher_name': 'Jane Doe',
            'sequencing_queue': ['X99999P001H05'],
            'open_date': '2016-09-01T13:00:00',
            'finished_date': None,
            'nb_quoted_samples': '2',
            'started_date': '2016-11-11T11:45:03.367000',
            'library_type': 'pcr_free',
            'nb_samples': 1,
            'species': 'Homo sapiens',
            'project_id': 'X99999'
        }
    ]

@mocked_get_sample_info
@mocked_get_samples_and_processes
@mocked_non_QC_queues
@mocked_request
@mocked_get_project_info
@mocked_retrieve_args
def test_sample_status_per_plate(mocked_retrieve_args,
                                 mocked_project_info,
                                 mocked_request,
                                 mocked_non_qc,
                                 mocked_samples_processes,
                                 mocked_sample_info):
    session = None
    s = sample_status_per_plate(session)
    assert s == [
        {
            'nb_samples': 1,
            'sequencing_queue': ['X99999P001H05'],
            'library_type': 'pcr_free',
            'plate_id': 'X99999P001',
            'species': 'Homo sapiens',
            'project_id': 'X99999'
        }
    ]
