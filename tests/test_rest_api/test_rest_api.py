import json
from collections import Counter, defaultdict
from datetime import datetime
from time import sleep
from unittest.mock import patch

import genologics_sql.tables as t

from config import rest_config as cfg
from rest_api import app
from rest_api.limsdb import get_session
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

        # Add stuff to the database
        cls.session = get_session()
        p1 = cls._create_project('testproject1', udfs={'Number of Quoted Samples': 9})
        p2 = cls._create_project('testproject2', udfs={'Number of Quoted Samples': 9}, closed=True)
        udfs = {'Required Yield (Gb)': 30, 'Coverage (X)': 15, 'Species': 'Gallus gallus'}
        s1 = cls._create_sample('sample1', p1, udfs=udfs)
        s2 = cls._create_sample('sample2', p1, udfs=udfs)
        udfs['Species'] = 'Homo Sapiens'
        p2s1 = cls._create_sample('sample5', p2, udfs=udfs)
        p2s2 = cls._create_sample('sample6', p2, udfs=udfs)
        p2s3 = cls._create_sample('sample7', p2, udfs=udfs)
        p2s4 = cls._create_sample('sample8', p2, udfs=udfs)

        a1 = cls._create_input_artifact(s1, 'plate1', 'H', '12')
        a2 = cls._create_input_artifact(s2, 'plate1', 'H', '11')
        step1 = cls._create_completed_process([a1], 'Awaiting User Response EG 2.0')
        step2 = cls._create_completed_process([a1], 'Random Step Name', create_date=datetime(2018, 1, 1))

        # Sample2 finishes once then get sequenced again then finishes again
        step3 = cls._create_completed_process([a2], 'AUTOMATED - Sequence', create_date=datetime(2018, 1, 1))
        step3 = cls._create_completed_process([a2], 'Data Release EG 2.0 ST', create_date=datetime(2018, 1, 15))
        step4 = cls._create_completed_process([a2], 'AUTOMATED - Sequence', create_date=datetime(2018, 2, 1))
        step5 = cls._create_completed_process([a2], 'Finish Processing EG 1.0 ST', create_date=datetime(2018, 2, 15))

        l1 = cls._create_input_artifact(p2s1, 'FLOWCELL1', '1', '1')
        l2 = cls._create_input_artifact(p2s2, 'FLOWCELL1', '1', '2')
        l3 = cls._create_input_artifact(p2s3, 'FLOWCELL1', '1', '3')
        l4 = cls._create_input_artifact(p2s4, 'FLOWCELL1', '1', '4')
        l5 = cls._create_input_artifact(p2s1, 'FLOWCELL1', '1', '5')
        l6 = cls._create_input_artifact(p2s2, 'FLOWCELL1', '1', '6')
        l7 = cls._create_input_artifact(p2s3, 'FLOWCELL1', '1', '7')
        l8 = cls._create_input_artifact(p2s4, 'FLOWCELL1', '1', '8')
        run1 = cls._create_completed_process([l1, l2, l3, l4, l5, l6, l7, l8], 'AUTOMATED - Sequence',
                                             create_date=datetime(2018, 3, 10), udfs={
                'Run Status': 'RunCompleted', 'RunID': 'date_machine1_counter_FLOWCELL1',
                'InstrumentID': 'machine1', 'Cycle': 310, 'Read': 3
            })

        cls.session.commit()

    @classmethod
    def _get_id(cls, klass):
        cls.all_ids[klass] += 1
        dbid = cls.all_ids[klass]
        return dbid

    @classmethod
    def _create_project(cls, name, udfs=None, closed=False):
        r = t.Researcher(firstname='Jane', lastname='Doe')
        p = t.Project(projectid=cls._get_id(t.Project), name=name, opendate=datetime(2018, 1, 23), researcher=r)
        if udfs:
            p.udfs = [cls._create_project_udf(k, v, p.projectid) for k, v in udfs.items()]
        if closed:
            p.closedate = datetime(2018, 2, 28)
        cls.session.add(p)
        cls.session.commit()
        return p

    @classmethod
    def _create_input_artifact(cls, sample, container_name, xpos, ypos, original=True):
        container = t.Container(containerid=cls._get_id(t.Container), name=container_name)
        placemment = t.ContainerPlacement(placementid=cls._get_id(t.ContainerPlacement), container=container,
                                          wellxposition=xpos, wellyposition=ypos)
        a = t.Artifact(artifactid=cls._get_id(t.Artifact), samples=[sample], containerplacement=placemment,
                       isoriginal=original)
        cls.session.add(a)
        cls.session.commit()
        return a

    @classmethod
    def _create_project_udf(cls, name, value, attachtoid):
        udf = t.EntityUdfView(
            udfname=name,
            udtname='udtname',
            udftype='udftype',
            udfunitlabel='unit',
            udfvalue=value,
            attachtoid=attachtoid,
            attachtoclassid=83
        )
        cls.session.add(udf)
        cls.session.commit()
        return udf

    @classmethod
    def _create_sample_udf(cls, name, value):
        udf = t.SampleUdfView(
            udfname=name,
            udtname='udtname',
            udftype='udftype',
            udfunitlabel='unit',
            udfvalue=value,
        )
        # Needs to add this udf to a sample
        return udf

    @classmethod
    def _create_process_udf(cls, process_type, name, value):
        udf = t.ProcessUdfView(
            udfname=name,
            typeid=process_type.typeid,
            udtname='udtname',
            udftype='udftype',
            udfunitlabel='unit',
            udfvalue=value,
        )
        # Needs to add this udf to a process
        return udf

    @classmethod
    def _create_sample(cls, name, project, udfs=None):
        p = t.Process(processid=cls._get_id(t.Process))
        s = t.Sample(processid=p.processid, sampleid=cls._get_id(t.Sample), name=name, project=project)
        if udfs:
            s.udfs = [cls._create_sample_udf(k, v) for k, v in udfs.items()]
        cls.session.add(p)
        cls.session.add(s)
        cls.session.commit()
        return s

    @classmethod
    def _create_completed_process(cls, list_artifacts, step_name, create_date=None, udfs=None):
        process_type = t.ProcessType(typeid=cls._get_id(t.ProcessType), displayname=step_name)
        process = t.Process(processid=cls._get_id(t.Process), type=process_type, workstatus='COMPLETE',
                            createddate=create_date or datetime(2018, 2, 10))
        for a in list_artifacts:
            t.ProcessIOTracker(trackerid=cls._get_id(t.ProcessIOTracker), artifact=a, process=process)
        if udfs:
            process.udfs = [cls._create_process_udf(process_type, k, v) for k, v in udfs.items()]
        cls.session.add(process)
        return process

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
                'researcher_name': 'Jane Doe'
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
                'researcher_name': 'Jane Doe'
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
                'library_queue': ['sample1'],
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
                'status': {'finished': {
                    'last_modified_date': '2018-02-15T00:00:00',
                    'samples': ['sample2']},
                    'library_queue': {
                        'last_modified_date': '2018-02-10T00:00:00',
                        'samples': ['sample1']}}
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
                'library_queue': ['sample1'],
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
                           'library_queue': {'last_modified_date': '2018-02-10T00:00:00',
                                             'samples': ['sample1']}}
            }]}
        assert json_of_response(response) == exp

    def test_lims_sample_status(self):
        response = self.client.get('/api/0.1/lims/sample_status?match={"sample_id":"sample1"}')
        assert response.status_code == 200
        exp = {
            '_meta': {'total': 1},
            'data': [{
                'current_status': 'library_queue',
                'finished_date': None,
                'library_type': None,
                'project_id': 'testproject1',
                'sample_id': 'sample1',
                'species': 'Gallus gallus',
                'started_date': None,
                'required_yield': '30',
                'required_coverage': '15',
                'statuses': [{
                    'date': 'Feb 10 2018',
                    'name': 'sample_submission',
                    'processes': [
                        {'date': 'Feb 10 2018', 'name': 'Awaiting User Response EG 2.0', 'process_id': 7,
                         'type': 'complete'}
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
            '_meta': {'total': 1},
            'data': [{
                'created_date': '2018-03-10T00:00:00',
                'cst_date': None,
                'instrument_id': 'machine1',
                'nb_cycles': '310',
                'nb_reads': '3',
                'project_ids': ['testproject2'],
                'run_id': 'date_machine1_counter_FLOWCELL1',
                'run_status': 'RunCompleted',
                'sample_ids': ['sample5', 'sample6', 'sample7', 'sample8']
            }]
        }
        assert_json_equal(json_of_response(response), exp)
