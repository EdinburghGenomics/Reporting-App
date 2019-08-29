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
        self.uniq_entities = defaultdict(dict)

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
            self.lims_objects['artifacts'][sample['name']] = self._create_artifact(**artifact)

        for artifact in data.get('artifacts'):
            if isinstance(artifact['samples'], list):
                artifact['samples'] = [self.lims_objects['samples'][s] for s in artifact['samples']]
            else:
                # Assume it's the sample name being provided instead of the list of name
                artifact['samples'] = [self.lims_objects['samples'][artifact['samples']]]
            artifact['original'] = False
            self.lims_objects['artifacts'][artifact['name']] = self._create_artifact(**artifact)

        for step in data.get('completed_steps'):
            step['list_artifacts'] = [self.lims_objects['artifacts'][a] for a in step['list_artifacts']]
            step['list_output_artifacts'] = [self.lims_objects['artifacts'][a] for a in step.get('list_output_artifacts', [])]
            self.lims_objects['steps'][step['name']] = self._create_completed_process(**step)
        self.session.commit()

    def _get_id(self, klass):
        """
        Generate a incremental id to be used when creating the sqlalchemy objects
        """
        self.all_ids[klass] += 1
        dbid = self.all_ids[klass]
        return dbid

    def _create_project(self, name, udfs=None, closed=False, researcher=None):
        """
        Create the sqlalchemy Project object. if researcher is not provided it also creates it with name Jane Doe.
        Creation date is always 23-Jan-2018. If closed closed date is 28-Feb-2018
        """
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

    def _create_artifact(self, name, samples, container_name=None, xpos=None, ypos=None, udfs=None, original=True,
                               reagent_labels=None, qcflag=0):
        """
        Create the sqlalchemy Artifact object.
        if container name is provided it creates it and place the artifact in the provided x and y pos.
        reagent label can also be added and so is the qcflag.
        """
        if container_name:
            container = t.Container(containerid=self._get_id(t.Container), name=container_name)
            placement = t.ContainerPlacement(placementid=self._get_id(t.ContainerPlacement), container=container,
                                              wellxposition=xpos, wellyposition=ypos)
        else:
            placemment = None
        artifact_state = t.ArtifactState(stateid=self._get_id(t.ArtifactState), qcflag=qcflag)
        a = t.Artifact(artifactid=self._get_id(t.Artifact), name=name, samples=samples, containerplacement=placemment,
                       isoriginal=original, states=[artifact_state])
        if udfs:
            a.udfs = [self._create_artifact_udf(k, v) for k, v in udfs.items()]

        # Add reagent_labels to the artifacts
        if reagent_labels:
            a.reagentlabels = [self._create_reagent_label(reagent_label) for reagent_label in reagent_labels]
        # Add the sample artifacts as ancestors to this artifact
        ancestors = [self.lims_objects['artifacts'][s.name] for s in samples if s.name in self.lims_objects['artifacts']]
        a.ancestors = ancestors
        self.session.add(a)
        return a

    def _create_project_udf(self, name, value, attachtoid):
        """Generate a UDF entity for a project."""
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
        """Generate a UDF entity for a sample."""
        udf = t.SampleUdfView(
            udfname=name,
            udtname='udtname',
            udftype='udftype',
            udfunitlabel='unit',
            udfvalue=value,
        )
        return udf

    def _create_artifact_udf(self, name, value):
        """Generate a UDF entity for an artifact."""
        udf = t.ArtifactUdfView(
            udfname=name,
            udtname='udtname',
            udftype='udftype',
            udfunitlabel='unit',
            udfvalue=value,
        )
        self.session.add(udf)
        return udf

    def _create_process_udf(self, process_type, name, value):
        """Generate a UDF entity for a process."""
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
        """Generate a Sample entity for an artifact"""
        p = t.Process(processid=self._get_id(t.Process))
        s = t.Sample(processid=p.processid, sampleid=self._get_id(t.Sample), name=name, project=project)
        if udfs:
            s.udfs = [self._create_sample_udf(k, v) for k, v in udfs.items()]
        self.session.add(p)
        self.session.add(s)
        return s

    def uniq_Lab_protocol(self, name, **kwargs):
        """Create a LabProtocol entity if it does not exist already."""
        if name not in self.uniq_entities[t.LabProtocol]:
            self.uniq_entities[t.LabProtocol][name] = t.LabProtocol(
                protocolid=self._get_id(t.LabProtocol),
                protocolname=name,
                **kwargs
            )
        return self.uniq_entities[t.LabProtocol].get(name)

    def _create_completed_process(self, list_artifacts, name, list_output_artifacts=None, created_date=None, udfs=None,
                                  labprotocol='Protocol'):
        """Create a Process entity using the provided name, list of artifact both input and output.
        It assumes 1:1 relationship between the input and output.
        The protocol name can be provided but defaults to "protocol" if not
        """
        process_type = t.ProcessType(typeid=self._get_id(t.ProcessType), displayname=name)
        if not labprotocol:
            labprotocol = name

        protocolstep = t.ProtocolStep(stepid=self._get_id(t.ProtocolStep),
                                      labprotocol=self.uniq_Lab_protocol(labprotocol),
                                      processtype=process_type)

        process = t.Process(processid=self._get_id(t.Process), type=process_type, workstatus='COMPLETE',
                            protocolstep=protocolstep, createddate=created_date or datetime(2018, 2, 10))
        # Create the input output linkage.
        # Assumes one output per input if output exists
        for i, a in enumerate(list_artifacts):
            if list_output_artifacts:
                output_artifacts = [t.OutputMapping(
                    mappingid=self._get_id(t.OutputMapping),
                    outputartifactid=list_output_artifacts[i].artifactid
                )]
            else:
                output_artifacts = []
            t.ProcessIOTracker(trackerid=self._get_id(t.ProcessIOTracker), artifact=a, output=output_artifacts,
                               process=process)
        if udfs:
            process.udfs = [self._create_process_udf(process_type, k, v) for k, v in udfs.items()]
        self.session.add(process)
        return process

    def _create_reagent_label(self, name):
        r = t.ReagentLabel(labelid=self._get_id(t.ReagentLabel), name=name)
        self.session.add(r)
        return r


if __name__ == "__main__":
    argparse = ArgumentParser()
    argparse.add_argument('--yaml_file', required=True)
    args = argparse.parse_args()
    DataAdder().add_data_from_yaml(args.yaml_file)
