import operator
from collections import defaultdict
from datetime import datetime

from egcg_core.clarity import sanitize_user_id
from flask import request, json

from rest_api.limsdb.queries import get_samples_and_processes, non_QC_queues, get_project_info, \
    get_sample_info
from config import project_status as status_cfg


class Sample:
    def __init__(self):
        self.completed_processes = []
        self.processes = []
        self.queue_location = {}
        self._status_and_date = None
        self.planned_library = None
        self.species = None

    def add_completed_process(self, process_name, completed_date):
        self.processes.append((process_name, completed_date, 'complete'))

    def add_queue_location(self, process_name, queued_date):
        self.processes.append((process_name, queued_date, 'queued'))

    def _get_status_and_date(self):
        if not self._status_and_date:
            self.processes.sort(key=operator.itemgetter(1), reverse=True)
            self._status_and_date = status_cfg.status_order[0], datetime.now()
            for process, date, process_type in self.processes:
                if process_type == 'complete' and process in status_cfg.step_completed_to_status:
                    finished_status = status_cfg.step_completed_to_status.get(process)
                    self._status_and_date = status_cfg.status_order[status_cfg.status_order.index(finished_status) + 1], date
                    break
                elif process_type == 'queued' and process in status_cfg.step_queued_to_status:
                    self._status_and_date = status_cfg.step_queued_to_status.get(process), date
                    break
        return self._status_and_date

    @property
    def additional_status(self):
        additional_status = set()
        for process, date, process_type in self.processes:
            if process_type == 'complete' and process in status_cfg.additional_step_completed:
                finished_status = status_cfg.additional_step_completed.get(process)
                additional_status.add(finished_status)
        return additional_status

    @property
    def library_type(self):
        for process, date, process_type in self.processes:
            if process_type == 'complete' and process in status_cfg.library_type_step_completed:
                return status_cfg.library_type_step_completed.get(process)
        return status_cfg.library_planned_alias.get(self.planned_library)

    @property
    def status(self):
        status, date = self._get_status_and_date()
        return status

    @property
    def status_date(self):
        status, date = self._get_status_and_date()
        return date

    @property
    def started_date(self):
        self.processes.sort(key=operator.itemgetter(1), reverse=True)
        for p in reversed(self.processes):
            process, date, process_type = p
            if process_type == 'complete':
                return date


class Container:
    def __init__(self):
        self.samples = defaultdict(Sample)
        self.project_id = None
        self.name = None

    def samples_per_status(self):
        sample_per_status = defaultdict(list)
        for sample_name in self.samples:
            sample_per_status[self.samples[sample_name].status].append(sample_name)
            for status in self.samples[sample_name].additional_status:
                sample_per_status[status].append(sample_name)
        return sample_per_status

    @property
    def library_types(self):
        return ', '.join(set([
                            self.samples[sample_name].library_type
                            for sample_name in self.samples
                            if self.samples[sample_name].library_type
                            ]))

    @property
    def species(self):
        return ', '.join(set([
                                 self.samples[sample_name].species
                                 for sample_name in self.samples
                                 if self.samples[sample_name].species
                                 ]))

    def to_json(self):
        ret = {
            'plate_id': self.name,
            'project_id': self.project_id,
            'library_type': self.library_types,
            'species': self.species
        }
        ret.update(self.samples_per_status())
        return ret


class Project(Container):
    def __init__(self):
        super().__init__()
        self.open_date = None
        self.researcher_name = None
        self.nb_quoted_samples = None

    def to_json(self):
        ret = {
            'project_id': self.name,
            'library_type': self.library_types,
            'species': self.species,
            'open_date': self.open_date,
            'researcher_name': self.researcher_name,
            'nb_quoted_samples': self.nb_quoted_samples,
            'finished_date': self.finished_date,
            'started_date': self.started_date
        }
        ret.update(self.samples_per_status())

        return ret

    @property
    def finished_date(self):
        finished_samples = [
                (sample_name, self.samples[sample_name].status_date)
                for sample_name in self.samples
                if self.samples[sample_name].status == status_cfg.status_names['FINISHED']
            ]
        if finished_samples and self.nb_quoted_samples and len(finished_samples) >= int(self.nb_quoted_samples):
            finished_samples.sort(key=operator.itemgetter(1))
            s, d = finished_samples[-1]
            return d.isoformat() + 'Z'
        return None

    @property
    def started_date(self):
        if self.samples:
            dates = sorted([
                              self.samples.get(sample_name).started_date
                              for sample_name in self.samples
                              if self.samples.get(sample_name).started_date
                           ])
            if dates:
                return dates[0]
        return None



def sample_status_per_project(session):
    """This function queries the lims database for sample information and aggregate at the project name level"""
    match = json.loads(request.args.get('match', '{}'))
    project_name = match.get('project_id')
    all_projects = defaultdict(Project)
    for project_info in get_project_info(session, project_name, udfs=['Number of Quoted Samples']):
        pjct_name, open_date, firstname, lastname, udf_name , nb_quoted_samples = project_info
        all_projects[pjct_name].name = pjct_name
        all_projects[pjct_name].open_date = open_date.isoformat() + 'Z'
        all_projects[pjct_name].researcher_name = '%s %s' % (firstname, lastname)
        all_projects[pjct_name].nb_quoted_samples = nb_quoted_samples

    for result in get_samples_and_processes(
            session,
            project_name,
            workstatus='COMPLETE',
            list_process=list(status_cfg.step_completed_to_status) \
                       + list(status_cfg.additional_step_completed) \
                       + list(status_cfg.library_type_step_completed)
    ):
        (pjct_name, sample_name, process_name, process_status, date_run) = result
        all_projects[pjct_name].samples[sanitize_user_id(sample_name)].add_completed_process(process_name, date_run)

    for result in non_QC_queues(session, project_name, list_process=status_cfg.step_queued_to_status):
        pjct_name, sample_name, process_name, queued_date = result
        all_projects[pjct_name].samples[sanitize_user_id(sample_name)].add_queue_location(process_name, queued_date)

    for result in get_sample_info(session, project_name, udfs=['Prep Workflow', 'Species']):
        (pjct_name, sample_name, container, wellx, welly, udf_name, udf_value) = result
        if udf_name == 'Prep Workflow':
            all_projects[pjct_name].samples[sanitize_user_id(sample_name)].planned_library = udf_value
        if udf_name == 'Species':
            all_projects[pjct_name].samples[sanitize_user_id(sample_name)].species = udf_value

    return [p.to_json() for p in all_projects.values()]


def sample_status_per_plate(session):
    """This function queries the lims database for sample information and aggregate at the plate name level"""
    match = json.loads(request.args.get('match', '{}'))
    project_name = match.get('project_id')
    all_plates = defaultdict(Container)
    sample_to_container = {}
    for result in get_sample_info(session, project_name, udfs=['Prep Workflow', 'Species']):
        (pjct_name, sample_name, container, wellx, welly, udf_name, udf_value) = result
        all_plates[container].name = container
        all_plates[container].project_id = pjct_name
        if udf_name == 'Prep Workflow':
            all_plates[container].samples[sanitize_user_id(sample_name)].planned_library = udf_value
        if udf_name == 'Species':
            all_plates[container].samples[sanitize_user_id(sample_name)].species = udf_value
        sample_to_container[sample_name] = container

    for result in get_samples_and_processes(
            session,
            project_name,
            workstatus='COMPLETE',
            list_process=list(status_cfg.step_completed_to_status) \
                       + list(status_cfg.additional_step_completed) \
                       + list(status_cfg.library_type_step_completed)
    ):
        (pjct_name, sample_name, process_name, process_status, date_run) = result
        container = sample_to_container.get(sample_name)
        all_plates[container].samples[sanitize_user_id(sample_name)].add_completed_process(process_name, date_run)

    for result in non_QC_queues(session, project_name, list_process=status_cfg.step_queued_to_status):
        pjct_name, sample_name, process_name, queued_date = result
        container = sample_to_container.get(sample_name)
        all_plates[container].samples[sanitize_user_id(sample_name)].add_queue_location(process_name, queued_date)

    return [p.to_json() for p in all_plates.values()]


