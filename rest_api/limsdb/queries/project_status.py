import operator
from collections import defaultdict
from datetime import datetime

from egcg_core.clarity import sanitize_user_id
from flask import request, json

from rest_api.limsdb.queries import get_samples_and_processes, non_QC_queues, get_project_info
from config import project_status as status_cfg

class Sample:
    def __init__(self):
        self.completed_processes = []
        self.processes = []
        self.queue_location = {}

    def add_completed_process(self, process_name, completed_date):
        self.processes.append((process_name, completed_date, 'complete'))

    def add_queue_location(self, process_name, queued_date):
        self.processes.append((process_name, queued_date, 'queued'))

    @property
    def status(self):
        self.processes.sort(key=operator.itemgetter(1), reverse=True)
        for process, date, type in self.processes:
            if type == 'complete' and process in status_cfg.step_completed_to_status:
                finished_status = status_cfg.step_completed_to_status.get(process)
                return status_cfg.status_order[status_cfg.status_order.index(finished_status) + 1]
            elif type == 'queued' and process in status_cfg.step_queued_to_status:
                return  status_cfg.step_queued_to_status.get(process)
        return status_cfg.status_order[0]

    @property
    def status_date(self):
        self.processes.sort(key=operator.itemgetter(1), reverse=True)
        for process, date, type in self.processes:
            if type == 'complete' and process in status_cfg.step_completed_to_status:
                return date
            elif type == 'queued' and process in status_cfg.step_queued_to_status:
                return date
        return datetime.now()


class Project:
    def __init__(self):
        self.samples = defaultdict(Sample)
        self.open_date = None
        self.researcher_name = None
        self.name = None
        self.nb_quoted_samples = None

    def samples_per_status(self):
        sample_per_status = defaultdict(list)
        for sample_name in self.samples:
            sample_per_status[self.samples[sample_name].status].append(sample_name)
        return sample_per_status

    def to_json(self):
        ret = {
            'project_id': self.name,
            'open_date': self.open_date,
            'researcher_name': self.researcher_name,
            'nb_quoted_samples': self.nb_quoted_samples
        }
        ret.update(self.samples_per_status())
        return ret


def sample_status_per_project(session):
    match = json.loads(request.args.get('match', '{}'))
    project_name = match.get('project_name')
    all_projects = defaultdict(Project)

    for project_info in get_project_info(session, project_name, udfs=['Number of Quoted Samples']):
        pjct_name, open_date, firstname, lastname, udf_name , nb_quoted_samples = project_info
        all_projects[pjct_name].name = pjct_name
        all_projects[pjct_name].open_date = open_date.isoformat() + 'Z'
        all_projects[pjct_name].researcher_name = '%s %s' % (firstname, lastname)
        all_projects[pjct_name].nb_quoted_samples = nb_quoted_samples

    for result in get_samples_and_processes(session, project_name, workstatus='COMPLETE',
                                            list_process=status_cfg.step_completed_to_status):
        (pjct_name, sample_name, process_name, process_status, date_run) = result
        all_projects[pjct_name].samples[sanitize_user_id(sample_name)].add_completed_process(process_name, date_run)

    for result in non_QC_queues(session, project_name, list_process=status_cfg.step_queued_to_status):
        pjct_name, sample_name, process_name, queued_date = result
        all_projects[pjct_name].samples[sanitize_user_id(sample_name)].add_queue_location(process_name, queued_date)

    return [p.to_json() for p in all_projects.values()]

def sample_info(session):
    #match = json.loads(request.args.get('match', '{}'))
    #sample_id = match.get('sample_id')
    sample_id = 'X16129P001D01'
    all_projects = defaultdict(Project)

    for result in  get_samples_and_processes(session, sample_name=sample_id):
        project_name, open_date, firstname, lastname, sample_name, process_name, process_status, date_run = result
        all_projects[project_name].samples[sanitize_user_id(sample_name)].processes[process_name] = date_run
        all_projects[project_name].name = project_name
        all_projects[project_name].open_date = open_date.isoformat() + 'Z'
        all_projects[project_name].researcher_name = '%s %s' % (firstname, lastname)



if __name__ == "__main__":
    from rest_api.limsdb import get_session

    session = get_session()
    sample_info(session)

