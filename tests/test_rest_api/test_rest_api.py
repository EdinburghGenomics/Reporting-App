import json
from collections import Counter
from datetime import datetime
from time import sleep
from unittest.mock import patch

from config import rest_config as cfg

from rest_api import app
from rest_api.limsdb import get_session
from tests.test_rest_api import TestBase
import genologics_sql.tables as t


def json_of_response(response):
    """Decode json from response"""
    return json.loads(response.data.decode('utf8'))


class TestLIMSRestAPI(TestBase):
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
        s1 = cls._create_sample('sample1', p1, udfs={'Required Yield': 3000})
        s2 = cls._create_sample('sample2', p2, udfs={'Required Yield': 3000})
        a1 = cls._create_artifact(s1, 'plate1', 'H', '12')
        a2 = cls._create_artifact(s2, 'plate1', 'H', '11')

        cls.session.commit()

    @classmethod
    def _get_id(cls, klass):
        cls.all_ids[klass] += 1
        id = cls.all_ids[klass]
        return id

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
    def _create_artifact(cls, sample, container_name, xpos, ypos, original=True):
        container = t.Container(containerid=cls._get_id(t.Container), name=container_name)
        placemment = t.ContainerPlacement(placementid=cls._get_id(t.ContainerPlacement), container=container,
                                          wellxposition=xpos, wellyposition=ypos)
        a = t.Artifact(artifactid=cls._get_id(t.Artifact), samples=[sample], containerplacement=placemment, isoriginal=original)
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
    def _create_sample(cls, name, project, udfs=None):
        p = t.Process(processid=cls._get_id(t.Process))
        s = t.Sample(processid=p.processid, sampleid=cls._get_id(t.Sample), name=name, project=project)
        if udfs:
            s.udfs = [cls._create_sample_udf(k, v) for k, v in udfs.items()]
        cls.session.add(p)
        cls.session.add(s)
        cls.session.commit()
        return s

    def test_lims_project_info(self):

        response = self.client.get('/api/0.1/lims/project_info')
        assert response.status_code == 200
        assert json_of_response(response) == {
            '_meta': {'total': 1},
            'data': [{
                'close_date': None,
                'nb_quoted_samples': '9',
                'open_date': '2018-01-23T00:00:00',
                'project_id': 'testproject1',
                'project_status': 'open',
                'researcher_name': 'Jane Doe'
            }]
        }
        response = self.client.get('/api/0.1/lims/project_info?match={"project_status": "closed"}')
        assert response.status_code == 200
        assert json_of_response(response) == {
            '_meta': {'total': 1},
            'data': [{
                'close_date': '2018-02-28T00:00:00',
                'nb_quoted_samples': '9',
                'open_date': '2018-01-23T00:00:00',
                'project_id': 'testproject2',
                'project_status': 'closed',
                'researcher_name': 'Jane Doe'
            }]
        }
        response = self.client.get('/api/0.1/lims/project_info?match={"project_status": "all"}')
        assert json_of_response(response)['_meta']['total'] == 2

    def test_lims_sample_info(self):
        response = self.client.get('/api/0.1/lims/sample_info')
        assert response.status_code == 200
        assert json_of_response(response) == {
            '_meta': {'total': 1},
            'data': [{
                'Required Yield': '3000',
                'plate_id': 'plate1',
                'project_id': 'testproject1',
                'sample_id': 'sample1'
            }]
        }
        response = self.client.get('/api/0.1/lims/sample_info?match={"project_status": "closed"}')
        assert response.status_code == 200
        assert json_of_response(response) == {
            '_meta': {'total': 1},
            'data': [{
                'Required Yield': '3000',
                'plate_id': 'plate1',
                'project_id': 'testproject2',
                'sample_id': 'sample2'
            }]
        }

    def test_other_endpoints(self):
        # only test that the enpoints exists
        # Additional test would require adding to the in memory sqlite database
        for endpoint in ['project_status', 'plate_status', 'sample_status', 'run_status']:
            response = self.client.get('/api/0.1/lims/' + endpoint)
            assert response.status_code == 200