from argparse import ArgumentParser
from collections import Counter, defaultdict
from datetime import datetime

import genologics_sql.tables as t
import yaml

from rest_api.limsdb import get_session


class DataAdder:

    def __init__(self):
        # Access to the database
        self.session = get_session()
        self.all_ids = Counter()
        self.lims_objects = defaultdict(dict)

    def add_data_from_yaml(self, yaml_file):
        """
        Create the object in sql alchemy from information from the yaml file.
        Projects, samples, artifacts and completed steps are created in this order.
        References between the entity is provided by their names:
        Sample contains a reference to its project
        Artifact contains a reference to its sample
        Steps contains references to the list of artifacts
        """
        with open(yaml_file) as open_file:
            data = yaml.safe_load(open_file)

        for project in data.get('projects'):
            if 'name' in project:
                self.lims_objects['projects'][project['name']] = self._create_project(**project)

        for sample in data.get('samples'):
            # Create the sample and the associated artifact based on provided artifact keyword
            sample['project'] = self.lims_objects['projects'][sample['project']]
            # extract the artifact information
            artifact = sample.pop('artifact')
            self.lims_objects['samples'][sample['name']] = self._create_sample(**sample)
            artifact['name'] = sample['name']
            artifact['samples'] = [self.lims_objects['samples'][sample['name']]]
            self.lims_objects['artifacts'][sample['name']] = self._create_input_artifact(**artifact)

        for artifact in data.get('artifacts'):
            if isinstance(artifact['samples'], list):
                artifact['samples'] = [self.lims_objects['samples'][s] for s in artifact['samples']]
            else:
                # Assume it's the sample name being provided instead of the list of name
                artifact['samples'] = [self.lims_objects['samples'][artifact['samples']]]
            artifact['original'] = False
            self.lims_objects['artifacts'][artifact['name']] = self._create_input_artifact(**artifact)

        for step in data.get('completed_steps'):
            step['list_artifacts'] = [self.lims_objects['artifacts'][a] for a in step['list_artifacts']]
            self.lims_objects['steps'][step['name']] = self._create_completed_process(**step)
        self.session.commit()

    def _get_id(self, klass):
        self.all_ids[klass] += 1
        dbid = self.all_ids[klass]
        return dbid

    def _create_project(self, name, udfs=None, closed=False, researcher=None):
        if researcher:
            r = researcher
        else:
            r = t.Researcher(firstname='Jane', lastname='Doe')
        p = t.Project(projectid=self._get_id(t.Project), name=name, opendate=datetime(2018, 1, 23), researcher=r)
        if udfs:
            p.udfs = [self._create_project_udf(k, v, p.projectid) for k, v in udfs.items()]
        if closed:
            p.closedate = datetime(2018, 2, 28)
        self.session.add(p)
        return p

    def _create_input_artifact(self, name, samples, container_name, xpos, ypos, original=True):
        container = t.Container(containerid=self._get_id(t.Container), name=container_name)
        placemment = t.ContainerPlacement(placementid=self._get_id(t.ContainerPlacement), container=container,
                                          wellxposition=xpos, wellyposition=ypos)
        a = t.Artifact(artifactid=self._get_id(t.Artifact), name=name, samples=samples, containerplacement=placemment,
                       isoriginal=original)
        self.session.add(a)
        return a

    def _create_project_udf(self, name, value, attachtoid):
        udf = t.EntityUdfView(
            udfname=name,
            udtname='udtname',
            udftype='udftype',
            udfunitlabel='unit',
            udfvalue=value,
            attachtoid=attachtoid,
            attachtoclassid=83
        )
        self.session.add(udf)
        return udf

    def _create_sample_udf(self, name, value):
        udf = t.SampleUdfView(
            udfname=name,
            udtname='udtname',
            udftype='udftype',
            udfunitlabel='unit',
            udfvalue=value,
        )
        return udf

    def _create_process_udf(self, process_type, name, value):
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

    def _create_sample(self, name, project, udfs=None):
        p = t.Process(processid=self._get_id(t.Process))
        s = t.Sample(processid=p.processid, sampleid=self._get_id(t.Sample), name=name, project=project)
        if udfs:
            s.udfs = [self._create_sample_udf(k, v) for k, v in udfs.items()]
        self.session.add(p)
        self.session.add(s)
        return s

    def _create_completed_process(self, list_artifacts, name, created_date=None, udfs=None):
        process_type = t.ProcessType(typeid=self._get_id(t.ProcessType), displayname=name)
        process = t.Process(processid=self._get_id(t.Process), type=process_type, workstatus='COMPLETE',
                            createddate=created_date or datetime(2018, 2, 10))
        for a in list_artifacts:
            t.ProcessIOTracker(trackerid=self._get_id(t.ProcessIOTracker), artifact=a, process=process)
        if udfs:
            process.udfs = [self._create_process_udf(process_type, k, v) for k, v in udfs.items()]
        self.session.add(process)
        return process


if __name__ == "__main__":
    argparse = ArgumentParser()
    argparse.add_argument('--yaml_file', required=True)
    args = argparse.parse_args()
    DataAdder().add_data_from_yaml(args.yaml_file)