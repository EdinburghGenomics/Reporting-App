import json
import os
from collections import Counter
from time import sleep
from unittest.mock import patch

from config import rest_config as cfg
from docker.load_data_to_lims_db import DataAdder
from rest_api import app
from tests.test_rest_api import TestBase


def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj


def json_of_response(response):
    """Decode json from response"""
    return json.loads(response.data.decode('utf8'))


def assert_json_equal(json1, json2):
    assert ordered(json1) == ordered(json2)


class TestLIMSRestAPI(TestBase):
    session = None
    sample_process_id = 10000
    all_ids = Counter()

    @classmethod
    def setUpClass(cls):
        app.testing = True
        cls.client = app.test_client()

        sleep(1)

        cls.patched_auth = patch('auth.DualAuth.authorized', return_value=True)
        cls.patched_auth.start()

        del cfg.content['lims_database']
        cls.data_adder = DataAdder()
        cls.data_adder.add_data_from_yaml(os.path.join(cls.assets_dir, 'data_for_clarity_lims.yaml'))

    def test_lims_project_info(self):
        response = self.client.get('/api/0.1/lims/project_info')
        assert response.status_code == 200
        assert_json_equal(json_of_response(response), {
            '_meta': {'total': 1},
            'data': [{
                'close_date': None,
                'nb_quoted_samples': '9',
                'open_date': '2018-01-23T00:00:00',
                'project_id': 'testproject1',
                'project_status': 'open',
                'researcher_name': 'Jane Doe',
                'udfs': {'Number of Quoted Samples': '9'}
            }]
        })
        response = self.client.get('/api/0.1/lims/project_info?match={"project_status": "closed"}')
        assert response.status_code == 200
        assert_json_equal(json_of_response(response), {
            '_meta': {'total': 1},
            'data': [{
                'close_date': '2018-02-28T00:00:00',
                'nb_quoted_samples': '9',
                'open_date': '2018-01-23T00:00:00',
                'project_id': 'testproject2',
                'project_status': 'closed',
                'researcher_name': 'Jane Doe',
                'udfs': {'Number of Quoted Samples': '9'}
            }]
        })
        response = self.client.get('/api/0.1/lims/project_info?match={"project_status": "all"}')
        assert json_of_response(response)['_meta']['total'] == 2

    def test_lims_sample_info(self):
        response = self.client.get('/api/0.1/lims/sample_info')
        assert response.status_code == 200
        exp = {
            '_meta': {'total': 2},
            'data': [
                {'Required Yield (Gb)': '30', 'Coverage (X)': '15', 'Species': 'Gallus gallus', 'plate_id': 'plate1',
                 'project_id': 'testproject1', 'sample_id': 'sample1'},
                {'Required Yield (Gb)': '30', 'Coverage (X)': '15', 'Species': 'Gallus gallus', 'plate_id': 'plate1',
                 'project_id': 'testproject1', 'sample_id': 'sample2'}
            ]
        }
        assert_json_equal(json_of_response(response), exp)
        response = self.client.get('/api/0.1/lims/sample_info?match={"project_status": "closed"}')
        assert response.status_code == 200
        assert json_of_response(response)['_meta']['total'] == 4

    def test_lims_project_status(self):
        response = self.client.get('/api/0.1/lims/project_status')
        assert response.status_code == 200
        exp = {
            '_meta': {'total': 1},
            'data': [{
                'close_date': None,
                'finished_date': None,
                'bioinformatics': ['sample1'],
                'finished': ['sample2'],
                'library_type': '',
                'nb_quoted_samples': '9',
                'nb_samples': 2,
                'open_date': '2018-01-23T00:00:00',
                'project_id': 'testproject1',
                'project_status': 'open',
                'researcher_name': 'Jane Doe',
                'species': 'Gallus gallus',
                'started_date': None,
                'required_yield': '30',
                'required_coverage': '15',
                'status': {
                    'finished': {'last_modified_date': '2018-02-15T00:00:00', 'samples': ['sample2'] },
                    'bioinformatics': {'last_modified_date': '2018-02-11T00:00:00', 'samples': ['sample1']}
                }
            }]
        }
        assert_json_equal(json_of_response(response), exp)

        response = self.client.get('/api/0.1/lims/project_status?match={"project_status": "all"}')
        assert response.status_code == 200
        assert json_of_response(response)['_meta']['total'] == 2

        response = self.client.get(
            '/api/0.1/lims/project_status?match={"project_id":"testproject2","project_status": "all"}')
        assert response.status_code == 200
        assert json_of_response(response)['_meta']['total'] == 1
        assert json_of_response(response)['data'][0]['project_id'] == 'testproject2'

    def test_lims_plate_status(self):
        response = self.client.get('/api/0.1/lims/plate_status')
        assert response.status_code == 200
        exp = {
            '_meta': {'total': 1},
            'data': [{
                'bioinformatics': ['sample1'],
                'finished': ['sample2'],
                'library_type': '',
                'nb_samples': 2,
                'plate_id': 'plate1',
                'project_id': 'testproject1',
                'species': 'Gallus gallus',
                'required_yield': '30',
                'required_coverage': '15',
                'status': {'finished': {'last_modified_date': '2018-02-15T00:00:00',
                                        'samples': ['sample2']},
                           'bioinformatics': {'last_modified_date': '2018-02-11T00:00:00',
                                             'samples': ['sample1']}}
            }]}
        assert_json_equal(json_of_response(response), exp)

    def test_lims_sample_status(self):
        response = self.client.get('/api/0.1/lims/sample_status?match={"sample_id":"sample1"}')
        assert response.status_code == 200
        exp = {
            '_meta': {'total': 1},
            'data': [{
                'current_status': 'bioinformatics',
                'finished_date': None,
                'library_type': None,
                'project_id': 'testproject1',
                'sample_id': 'sample1',
                'species': 'Gallus gallus',
                'started_date': None,
                'required_yield': '30',
                'required_coverage': '15',
                'statuses': [
                    {
                        'name': 'sample_submission',
                        'date': 'Feb 10 2018',
                        'processes': [
                            {'name': 'Awaiting User Response EG 2.0', 'date': 'Feb 10 2018', 'type': 'complete', 'process_id': 7}
                        ]},
                    {
                        'name': 'library_queue',
                        'date': 'Feb 11 2018',
                        'processes': [
                            {'name': 'AUTOMATED - Sequence', 'date': 'Feb 11 2018', 'type': 'complete', 'process_id': 12}
                        ]
                    }
                ]
            }]
        }

        assert_json_equal(json_of_response(response), exp)

        response = self.client.get('/api/0.1/lims/sample_status?match={"sample_id":"sample1"}&detailed=true')
        assert json_of_response(response)['_meta']['total'] == 1
        assert len(json_of_response(response)['data'][0]['statuses'][0]['processes']) == 2

    def test_lims_sample_finish_date(self):
        response = self.client.get('/api/0.1/lims/sample_status?match={"sample_id":"sample2"}')
        assert response.status_code == 200

        # finished data for sample2 is the first time it went through the finished status
        assert json_of_response(response)['data'][0]['finished_date'] == '2018-01-15T00:00:00'

    def test_lims_run_status(self):
        response = self.client.get('/api/0.1/lims/run_status')
        assert response.status_code == 200

        exp = {
            '_meta': {'total': 1}, 'data': [{
                'created_date': '2018-02-11T00:00:00', 'cst_date': None, 'run_id': 'date_machine1_counter_FLOWCELL1',
                'run_status': 'RunCompleted', 'sample_ids': ['sample1', 'sample2', 'sample3', 'sample4', 'sample5', 'sample6'],
                'project_ids': ['testproject1', 'testproject2'],
                'lanes': [
                    {'lane': 1, 'samples': [{'sample_id': 'sample1', 'barcode': '001A IDT-ILMN TruSeq DNA-RNA UD 96 Indexes  Plate_UDI0001 (GAGATTCC-ATAGAGGC)'}]},
                    {'lane': 2, 'samples': [{'sample_id': 'sample2', 'barcode': 'D703-D502 (CGCTCATT-ATAGAGGC)'}]},
                    {'lane': 3, 'samples': [{'sample_id': 'sample3', 'barcode': 'D704-D502 (GAGATTCC-ATAGAGGC)'}]},
                    {'lane': 4, 'samples': [{'sample_id': 'sample4', 'barcode': 'D701-D502 (ATTACTCG-ATAGAGGC)'}]},
                    {'lane': 5, 'samples': [{'sample_id': 'sample5', 'barcode': 'D707-D502 (CTGAAGCT-ATAGAGGC)'}]},
                    {'lane': 6, 'samples': [{'sample_id': 'sample6', 'barcode': 'D708-D502 (TAATGCGC-ATAGAGGC)'}]},
                    {'lane': 7, 'samples': [{'sample_id': 'sample2', 'barcode': 'D703-D502 (CGCTCATT-ATAGAGGC)'},
                                            {'sample_id': 'sample1', 'barcode': '001A IDT-ILMN TruSeq DNA-RNA UD 96 Indexes  Plate_UDI0001 (GAGATTCC-ATAGAGGC)'}]},
                    {'lane': 8, 'samples': [{'sample_id': 'sample3', 'barcode': 'D704-D502 (GAGATTCC-ATAGAGGC)'},
                                            {'sample_id': 'sample4', 'barcode': 'D701-D502 (ATTACTCG-ATAGAGGC)'}]}
                ],
                'instrument_id': 'machine1',
                'nb_reads': '3',
                'nb_cycles': '310'
            }]
        }
        assert_json_equal(json_of_response(response), exp)

    def test_libraries(self):
        response = self.client.get('/api/0.1/lims/library_info')
        assert response.status_code == 200
        exp = {
            '_meta': {'total': 1},
            'data': [
                {
                    'id': 'LP123456',
                     'step_link': 'http://clarity.com/clarity/work-complete/14',
                     'step_run': 1,
                     'date_completed': None,
                     'samples': [
                        {'name': 'sample3', 'location': 'B:2', 'qc_flag': 'UNKNOWN', 'project_id': 'testproject2',
                         'udfs': {'Original Conc. (nM)': '5', 'Species': 'Homo Sapiens','Raw CP': '167'}},
                        {'name': 'sample4', 'location': 'C:2', 'qc_flag': 'UNKNOWN', 'project_id': 'testproject2',
                         'udfs': {'Original Conc. (nM)': '5', 'Species': 'Homo Sapiens','Raw CP': '167'}},
                        {'name': 'sample5', 'location': 'D:2', 'qc_flag': 'UNKNOWN', 'project_id': 'testproject2',
                         'udfs': {'Original Conc. (nM)': '5', 'Species': 'Homo Sapiens','Raw CP': '167'}},
                        {'name': 'sample6', 'location': 'E:2', 'qc_flag': 'UNKNOWN', 'project_id': 'testproject2',
                         'udfs': {'Original Conc. (nM)': '5', 'Species': 'Homo Sapiens','Raw CP': '167'}}
                    ],
                    'protocol': 'Test',
                    'nsamples': 4,
                    'pc_qc_flag_pass': 0.0,
                    'project_ids': ['testproject2']
                }
            ]
        }
        assert_json_equal(json_of_response(response), exp)

        response = self.client.get('/api/0.1/lims/library_info?match={"sample_id":"sample5"}')
        exp = {
            '_meta': {'total': 1},
            'data': [
                {
                    'id': 'LP123456',
                     'step_link': 'http://clarity.com/clarity/work-complete/14',
                     'step_run': 1,
                     'date_completed': None,
                     'samples': [
                        {'name': 'sample5', 'location': 'D:2', 'qc_flag': 'UNKNOWN', 'project_id': 'testproject2',
                         'udfs': {'Original Conc. (nM)': '5', 'Species': 'Homo Sapiens','Raw CP': '167'}},
                    ],
                    'protocol': 'Test',
                    'nsamples': 1,
                    'pc_qc_flag_pass': 0.0,
                    'project_ids': ['testproject2']
                }
            ]
        }
        assert_json_equal(json_of_response(response), exp)

    def test_genotyping(self):
        response = self.client.get('/api/0.1/lims/genotyping_info')
        assert response.status_code == 200
        exp = {
            '_meta': {'total': 1},
            'data': [{
                'id': 'GEN00001',
                 'step_link': 'http://clarity.com/clarity/work-complete/15', 'step_run': 1,
                 'date_completed': None,
                 'samples': [
                     {'name': 'sample3', 'location': 'B:2', 'qc_flag': 'UNKNOWN', 'project_id': 'testproject2',
                      'udfs': {'Number of Calls (This Run)': '26', 'Number of Calls (Best Run)': '26'}},
                     {'name': 'sample4', 'location': 'C:2', 'qc_flag': 'UNKNOWN', 'project_id': 'testproject2',
                      'udfs': {'Number of Calls (This Run)': '21', 'Number of Calls (Best Run)': '26'}}
                 ],
                'protocol': 'Test',
                'nsamples': 2,
                'pc_qc_flag_pass': 0.0,
                'project_ids': ['testproject2']
            }]
        }
        assert_json_equal(json_of_response(response), exp)

        response = self.client.get('/api/0.1/lims/genotyping_info?flatten=true')
        exp = {
            '_meta': {'total': 2},
            'data': [
                {
                    'id': 'GEN00001',
                    'step_link': 'http://clarity.com/clarity/work-complete/15',
                    'step_run': 1,
                    'date_completed': None,
                    'protocol': 'Test',
                    'project': 'testproject2',
                    'name': 'sample3',
                    'location': 'B:2',
                    'udfs': {'Number of Calls (This Run)': '26', 'Number of Calls (Best Run)': '26'},
                    'qc_flag': 'UNKNOWN',
                    'project_id': 'testproject2'
                },
                {
                    'id': 'GEN00001',
                    'step_link': 'http://clarity.com/clarity/work-complete/15',
                    'step_run': 1,
                    'date_completed': None,
                    'protocol': 'Test',
                    'project': 'testproject2',
                    'name': 'sample4',
                    'location': 'C:2',
                    'udfs': {'Number of Calls (This Run)': '21', 'Number of Calls (Best Run)': '26'},
                    'qc_flag': 'UNKNOWN',
                    'project_id': 'testproject2'
                }
            ]
        }
        assert_json_equal(json_of_response(response), exp)







