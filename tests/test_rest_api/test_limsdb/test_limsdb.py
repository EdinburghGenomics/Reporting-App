from unittest.case import TestCase
from datetime import datetime
from rest_api.limsdb.queries.sample_status import Sample
from tests.test_rest_api.test_aggregation import TestAggregation, FakeRequest
from unittest.mock import Mock, patch
from rest_api.aggregation import database_side
from rest_api.aggregation.database_side import stages as s


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
        self.sample1._processes.remove(('Test Process', datetime(2011, 1, 1, 0, 0), 'complete', None))

    def test_add_queue_location(self):
        self.sample1.add_queue_location('Test Process', datetime.strptime('01-01-11', '%d-%m-%y'))

        assert self.sample1._processes == {('Receive Sample EG 6.1', datetime(2015, 6, 1, 0, 0), 'complete', None),
                                           ('Read and Eval SSQC', datetime(2015, 7, 16, 0, 0), 'complete', None),
                                           ('Test Process', datetime(2011, 1, 1, 0, 0), 'queued', None)}

        self.sample1._processes.remove(('Test Process', datetime(2011, 1, 1, 0, 0), 'queued', None))

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
        assert len(all_status) == 2
        self.sample1._all_statuses_and_date = None
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

        self.sample1._processes.remove(('Sequencing Plate Preparation EG 2.0', datetime(2015, 7, 20, 0, 0), 'queued', None))

    def test_get_status_and_date(self):
        status_and_date = self.sample1._get_status_and_date()
        assert status_and_date == ('sample_qc', datetime(2015, 6, 1, 0, 0))
        self.sample1.add_queue_location('Sequencing Plate Preparation EG 2.0', datetime.strptime('20-07-15', '%d-%m-%y'))
        self.sample1._status_and_date = None
        status_and_date = self.sample1._get_status_and_date()
        assert status_and_date == ('library_queue', datetime(2015, 7, 20, 0, 0))
        self.sample1._processes.remove(('Sequencing Plate Preparation EG 2.0', datetime(2015, 7, 20, 0, 0), 'queued', None))

    def test_additional_status(self):
        additional_status = self.sample1.additional_status
        assert additional_status == set()
        self.sample1.add_completed_process('QuantStudio Data Import EG 1.0', datetime.strptime('20-07-15', '%d-%m-%y'))
        additional_status = self.sample1.additional_status
        assert additional_status == {'genotyped'}
        self.sample1._processes.remove(('QuantStudio Data Import EG 1.0', datetime(2015, 7, 20, 0, 0), 'complete', None))

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
