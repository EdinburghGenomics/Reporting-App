from collections import defaultdict
from egcg_core.clarity import sanitize_user_id
from flask import request
from config import project_status as status_cfg
from rest_api.common import retrieve_args
from rest_api.limsdb import queries
from rest_api.limsdb.queries.data_models import ProjectInfo, SampleInfo, Container, Run, Sample, Project


def _create_samples_info(session, match):
    """This function queries the lims database for sample information and create SampleInfo objects"""
    all_samples = defaultdict(SampleInfo)
    project_id = match.get('project_id')
    project_status = match.get('project_status', 'open')
    sample_id = match.get('sample_id')
    time_since = match.get('createddate')

    for result in queries.get_sample_info(session, project_id, sample_id, time_since=time_since, udfs='all',
                                          project_status=project_status):
        (pjct_name, sample_name, container, wellx, welly, udf_name, udf_value) = result
        s = all_samples[sanitize_user_id(sample_name)]
        s.sample_name = sanitize_user_id(sample_name)
        s.project_name = pjct_name
        s.plate_name = container
        s.original_name = sample_name
        s.udfs[udf_name] = udf_value

    return all_samples.values()


def _create_samples(session, match):
    """This function queries the lims database for sample information and create Sample objects"""
    all_samples = defaultdict(Sample)
    project_id = match.get('project_id')
    project_status = match.get('project_status', 'open')
    sample_id = match.get('sample_id')
    sample_time_since = match.get('createddate')
    detailed = request.args.get('detailed') in ['true', 'True',  True]
    if detailed:
        list_process_complete = None
        list_process_queued = None
    else:
        list_process_complete = list(status_cfg.step_completed_to_status) \
                       + list(status_cfg.additional_step_completed) \
                       + list(status_cfg.library_type_step_completed) \
                       + status_cfg.started_steps
        list_process_queued = status_cfg.step_queued_to_status

    for result in queries.get_sample_info(session, project_id, sample_id, project_status=project_status,
                                          time_since=sample_time_since, udfs=['Prep Workflow', 'Species']):
        (pjct_name, sample_name, container, wellx, welly, udf_name, udf_value) = result
        s = all_samples[sanitize_user_id(sample_name)]
        s.sample_name = sanitize_user_id(sample_name)
        s.project_name = pjct_name
        s.plate_name = container
        s.original_name = sample_name

        if udf_name == 'Prep Workflow':
            all_samples[sanitize_user_id(sample_name)].planned_library = udf_value
        if udf_name == 'Species':
            all_samples[sanitize_user_id(sample_name)].species = udf_value

    for result in queries.get_samples_and_processes(session,  project_id, sample_id, project_status=project_status,
                                                    workstatus='COMPLETE', list_process=list_process_complete,
                                                    time_since=sample_time_since):
        (pjct_name, sample_name, process_name, process_status, date_run, process_id) = result
        all_samples[sanitize_user_id(sample_name)].add_completed_process(process_name, date_run, process_id)

    for result in queries.get_sample_in_queues_or_progress(
            session, project_id, sample_id, list_process=list_process_queued,
            time_since=sample_time_since, project_status=project_status):
        pjct_name, sample_name, process_name, queued_date, queue_id, process_id, process_date = result
        if not process_id:
            all_samples[sanitize_user_id(sample_name)].add_queue_location(process_name, queued_date, queue_id)
        else:
            all_samples[sanitize_user_id(sample_name)].add_inprogress(process_name, process_date, process_id)

    return all_samples.values()


def sample_status(session):
    """This function queries the lims database for sample information and return json representation"""
    kwargs = retrieve_args()
    samples = _create_samples(session, kwargs.get('match', {}))
    return [s.to_json() for s in samples]


def sample_status_per_project(session):
    """This function queries the lims database for sample information and aggregate at the project name level"""
    kwargs = retrieve_args()
    match = kwargs.get('match', {})
    samples = _create_samples(session, match)
    project_name = match.get('project_id')
    project_status = match.get('project_status', 'open')
    all_projects = defaultdict(Project)
    for project_info in queries.get_project_info(session, project_name, udfs=['Number of Quoted Samples'],
                                                 project_status=project_status):
        pjct_name, open_date, close_date, firstname, lastname, udf_name, nb_quoted_samples = project_info
        all_projects[pjct_name].project_id = pjct_name
        all_projects[pjct_name].open_date = open_date
        all_projects[pjct_name].close_date = close_date
        all_projects[pjct_name].researcher_name = '%s %s' % (firstname, lastname)
        all_projects[pjct_name].nb_quoted_samples = nb_quoted_samples

    for sample in samples:
        all_projects[sample.project_name].samples.append(sample)

    return [p.to_json() for p in all_projects.values()]


def sample_status_per_plate(session):
    """This function queries the lims database for sample information and aggregate at the plate name level"""
    kwargs = retrieve_args()
    match = kwargs.get('match', {})
    samples = _create_samples(session, match)
    all_plates = defaultdict(Container)
    for sample in samples:
        all_plates[sample.plate_name].samples.append(sample)
        all_plates[sample.plate_name].container_name = sample.plate_name
        all_plates[sample.plate_name].project_id = sample.project_name

    return [p.to_json() for p in all_plates.values()]


def sample_info(session):
    """This function queries the lims database for sample information and return json representation"""
    kwargs = retrieve_args()
    samples = _create_samples_info(session, kwargs.get('match', {}))
    return [s.to_json() for s in samples]


def project_info(session):
    """This function queries the lims database for sample information and aggregate at the project name level"""
    kwargs = retrieve_args()
    match = kwargs.get('match', {})
    project_name = match.get('project_id')
    project_status = match.get('project_status', 'open')
    all_projects = defaultdict(ProjectInfo)
    for info in queries.get_project_info(session, project_name, udfs=['Number of Quoted Samples'],
                                         project_status=project_status):
        pjct_name, open_date, close_date, firstname, lastname, udf_name, nb_quoted_samples = info
        all_projects[pjct_name].project_id = pjct_name
        all_projects[pjct_name].open_date = open_date
        all_projects[pjct_name].close_date = close_date
        all_projects[pjct_name].researcher_name = '%s %s' % (firstname, lastname)
        all_projects[pjct_name].nb_quoted_samples = nb_quoted_samples

    return [p.to_json() for p in all_projects.values()]


def run_status(session):
    kwargs = retrieve_args()
    time_since = kwargs.get('createddate', None)
    status = kwargs.get('status', None)
    all_runs = defaultdict(Run)

    for data in queries.runs_info(session, time_since=time_since):
        createddate, process_id, udf_name, udf_value, lane, sample_id, project_id = data
        run = all_runs[process_id]
        run.created_date = createddate
        run.udfs[udf_name] = udf_value
        run.samples.add(sample_id)
        run.projects.add(project_id)
    for data in queries.runs_cst(session, time_since=time_since):
        process_id, cst_process_id, cst_date = data
        run = all_runs[process_id]
        run.cst_date = cst_date

    filterer = lambda r: True
    if status == 'current':
        filterer = lambda r: r.udfs['Run Status'] == 'RunStarted'
    elif status == 'recent':
        filterer = lambda r: r.udfs['Run Status'] != 'RunStarted'

    return sorted((r.to_json() for r in all_runs.values() if filterer(r)), key=lambda r: r['created_date'])
