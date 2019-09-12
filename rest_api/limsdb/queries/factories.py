from collections import defaultdict
from egcg_core.util import query_dict
from egcg_core.clarity import sanitize_user_id
from flask import request
from config import project_status as status_cfg
from rest_api.common import retrieve_args
from rest_api.limsdb import queries
from rest_api.limsdb.queries import data_models


def _create_samples_info(session, match):
    """Query the LIMS database for sample information and create SampleInfo objects"""
    all_samples = defaultdict(data_models.SampleInfo)
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
    """Query the LIMS database for sample information and create Sample objects"""
    all_samples = defaultdict(data_models.Sample)
    project_id = match.get('project_id')
    project_status = match.get('project_status', 'open')
    sample_id = match.get('sample_id')
    sample_time_since = match.get('createddate')
    process_limit_date = match.get('process_limit_date')
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
    udfs_to_fields = {
        'Prep Workflow': 'planned_library',
        'Species': 'species',
        'Required Yield (Gb)': 'required_yield',
        'Coverage (X)': 'coverage'
    }
    for result in queries.get_sample_info(session, project_id, sample_id, project_status=project_status,
                                          time_since=sample_time_since, udfs=list(udfs_to_fields)):
        (pjct_name, sample_name, container, wellx, welly, udf_name, udf_value) = result
        s = all_samples[sanitize_user_id(sample_name)]
        s.sample_name = sanitize_user_id(sample_name)
        s.project_name = pjct_name
        s.plate_name = container
        s.original_name = sample_name
        if udf_name in udfs_to_fields:
            setattr(all_samples[sanitize_user_id(sample_name)], udfs_to_fields[udf_name], udf_value)

    for result in queries.get_samples_and_processes(session,  project_id, sample_id, project_status=project_status,
                                                    workstatus='COMPLETE', list_process=list_process_complete,
                                                    time_since=sample_time_since, process_limit_date=process_limit_date):
        (pjct_name, sample_name, process_name, process_status, date_run, process_id) = result
        all_samples[sanitize_user_id(sample_name)].add_completed_process(process_name, date_run, process_id)

    for result in queries.get_sample_in_queues_or_progress(
            session, project_id, sample_id, list_process=list_process_queued,
            time_since=sample_time_since, project_status=project_status, process_limit_date=process_limit_date):
        pjct_name, sample_name, process_name, queued_date, queue_id, process_id, process_date = result
        if not process_id:
            all_samples[sanitize_user_id(sample_name)].add_queue_location(process_name, queued_date, queue_id)
        else:
            all_samples[sanitize_user_id(sample_name)].add_inprogress(process_name, process_date, process_id)

    return all_samples.values()


def sample_status(session):
    """Query the LIMS database for sample information and return json representations"""
    kwargs = retrieve_args()
    samples = _create_samples(session, kwargs.get('match', {}))
    return [s.to_json() for s in samples]


def sample_status_per_project(session):
    """Query the LIMS database for sample information and aggregate at the project name level"""
    kwargs = retrieve_args()
    match = kwargs.get('match', {})
    samples = _create_samples(session, match)
    project_name = match.get('project_id')
    project_status = match.get('project_status', 'open')
    all_projects = defaultdict(data_models.Project)
    for project_info in queries.get_project_info(session, project_name, udfs=['Number of Quoted Samples'],
                                                 project_status=project_status):
        pjct_name, open_date, close_date, firstname, lastname, udf_name, udf_value = project_info
        all_projects[pjct_name].project_id = pjct_name
        all_projects[pjct_name].open_date = open_date
        all_projects[pjct_name].close_date = close_date
        all_projects[pjct_name].researcher_name = '%s %s' % (firstname, lastname)
        all_projects[pjct_name].udfs[udf_name] = udf_value

    for sample in samples:
        all_projects[sample.project_name].samples.append(sample)

    return [p.to_json() for p in all_projects.values()]


def sample_status_per_plate(session):
    """Query the LIMS database for sample information and aggregate at the plate name level"""
    kwargs = retrieve_args()
    match = kwargs.get('match', {})
    samples = _create_samples(session, match)
    all_plates = defaultdict(data_models.Container)
    for sample in samples:
        all_plates[sample.plate_name].samples.append(sample)
        all_plates[sample.plate_name].container_name = sample.plate_name
        all_plates[sample.plate_name].project_id = sample.project_name

    return [p.to_json() for p in all_plates.values()]


def sample_info(session):
    """Query the LIMS database for sample information and return json representation"""
    kwargs = retrieve_args()
    samples = _create_samples_info(session, kwargs.get('match', {}))
    return [s.to_json() for s in samples]


def project_info(session):
    """Query the LIMS database for sample information and aggregate at the project name level"""
    kwargs = retrieve_args()
    match = kwargs.get('match', {})
    project_name = match.get('project_id')
    project_status = match.get('project_status', 'open')
    all_projects = defaultdict(data_models.ProjectInfo)
    for info in queries.get_project_info(session, project_name, udfs='all',
                                         project_status=project_status):
        pjct_name, open_date, close_date, firstname, lastname, udf_name, udf_value = info
        all_projects[pjct_name].project_id = pjct_name
        all_projects[pjct_name].open_date = open_date
        all_projects[pjct_name].close_date = close_date
        all_projects[pjct_name].researcher_name = '%s %s' % (firstname, lastname)
        all_projects[pjct_name].udfs[udf_name] = udf_value

    return [p.to_json() for p in all_projects.values()]


def _resolve_artifact_reagent_labels(session, artifact_ids):
    """
    This function takes a list of artifact ids and return for each artifact the sample and reagent label pair.
    If the artifact id correspond to a pool, it resolve multiple sample/reagent label pairs.
    Otherwise it only returns one.
    """
    res = queries.artifact_reagent_labels(session, artifact_ids)
    artifact_to_label = defaultdict(set)
    for r in res:
        artifact_id, ancestor_id, reagent_label, sample_name = r
        artifact_to_label[(artifact_id, ancestor_id)].add((artifact_id, reagent_label, sample_name))
    return set([
        artifact_to_label[(artifact_id, ancestor_id)].pop()
        for (artifact_id, ancestor_id) in artifact_to_label
        if len(artifact_to_label[(artifact_id, ancestor_id)]) == 1
    ])


def run_status(session):
    """Query the LIMS database for run information"""
    kwargs = retrieve_args()
    time_since = kwargs.get('createddate', None)
    status = kwargs.get('status', None)
    match = kwargs.get('match', {})
    run_id = match.get('run_id')
    run_ids = match.get('run_ids')
    if run_id:
        run_ids = [run_id]

    all_runs = defaultdict(data_models.Run)
    all_lanes = {}
    sample2project = {}
    for data in queries.runs_info(session, time_since=time_since, run_ids=run_ids):
        createddate, process_id, udf_name, udf_value, lane, artifact_id, sample_id, project_id = data
        run = all_runs[process_id]
        run.created_date = createddate
        run.udfs[udf_name] = udf_value
        if artifact_id not in all_lanes:
            run.lanes[artifact_id] = {'lane': lane + 1, 'samples': []}
            all_lanes[artifact_id] = run.lanes[artifact_id]
        else:
            run.lanes[artifact_id] = all_lanes[artifact_id]
        run.samples.add(sample_id)
        run.projects.add(project_id)
        sample2project[sample_id] = project_id

    for data in _resolve_artifact_reagent_labels(session, list(all_lanes)):
        artifact_id, barcode, sample_id = data
        all_lanes[artifact_id]['samples'].append({'project_id': sample2project[sample_id], 'sample_id': sample_id, 'barcode': barcode})

    for data in queries.runs_cst(session, time_since=time_since, run_ids=run_ids):
        process_id, cst_process_id, cst_date = data
        run = all_runs[process_id]
        run.cst_date = cst_date

    filterer = lambda r: True
    if status == 'current':
        filterer = lambda r: r.udfs['Run Status'] == 'RunStarted'
    elif status == 'recent':
        filterer = lambda r: r.udfs['Run Status'] != 'RunStarted'
    return sorted((r.to_json() for r in all_runs.values() if filterer(r)), key=lambda r: r['created_date'])


def step_info(session, step_name, artifact_udfs=None, sample_udfs=None, output_udfs=None, container_type='96 wells plate'):
    kwargs = retrieve_args()
    time_from = kwargs.get('time_from')
    time_to = kwargs.get('time_to')
    library_id = query_dict(kwargs, 'match.container_id')
    project_name = query_dict(kwargs, 'match.project_id')
    sample_name = query_dict(kwargs, 'match.sample_id')
    flatten = kwargs.get('flatten', False) in ['True', 'true', True]
    if container_type == '96 wells plate':
        y_coords = 'ABCDEFGH'
    elif container_type == '384 wells plate':
        y_coords = 'ABCDEFGHIJKLMNOP'
    else:
        # For tube the coordinate should be always '1:1'
        y_coords = '1'
    all_step_containers = defaultdict(data_models.StepContainer)
    for data in queries.step_info(session, step_name, time_from=time_from, time_to=time_to, container_name=library_id,
                                  project_name=project_name, sample_name=sample_name, artifact_udfs=artifact_udfs,
                                  sample_udfs=sample_udfs, output_udfs=output_udfs):

        luid, daterun, container_id, protocol_name, state_qc, state_modified, sample_id, project_id, wellx, welly = data[:10]

        step_container = all_step_containers[container_id]
        step_container.id = container_id
        step_container.type = protocol_name
        specific_step = step_container.specific_steps[luid]
        specific_step.id = luid
        specific_step.date_run = daterun
        location = '%s:%s' % (y_coords[welly], wellx + 1)

        artifact = specific_step.artifacts[location]
        artifact.name = sample_id
        artifact.states[state_modified] = state_qc
        artifact.project_id = project_id
        artifact.location = location
        # Whatever the number of udf type they will come at the end and come on key, value pair
        for i in range(10, len(data), 2):
            artifact.udfs[data[i]] = data[i+1]

    if flatten:
        return sorted((item for l in all_step_containers.values() for item in l.to_flatten_json()), key=lambda l: l['id'])
    else:
        return sorted((l.to_json() for l in all_step_containers.values()), key=lambda l: l['id'])


def library_info(session):
    art_udfs = ['Original Conc. (nM)', 'Sample Transfer Volume (uL)', 'TSP1 Transfer Volume (uL)', '%CV',
            'NTP Volume (uL)', 'Raw CP', 'RSB Transfer Volume (uL)', 'NTP Transfer Volume (uL)', 'Ave. Conc. (nM)',
            'Adjusted Conc. (nM)', 'Original Conc. (nM)', 'Sample Transfer Volume (uL)',
            'TSP1 Transfer Volume (uL)']
    smp_udfs = ['Species', 'Picogreen Concentration (ng/ul)', 'Total DNA (ng)', 'GQN']
    return step_info(session, 'Eval qPCR Quant', artifact_udfs=art_udfs, sample_udfs=smp_udfs)


def sample_qc_info(session):
    # Species is not required to be added in the list of UDFs, but in order to ensure that the sample is reported on,
    # at least one of the UDFs needs to be found and some test sample does not have the other ones
    # The Query becomes very slow if we allow for the sample to be reported even without a UDF.
    smp_udfs = ['Species', 'Picogreen Concentration (ng/ul)', 'Total DNA (ng)', 'GQN']
    return step_info(session, 'QC Review EG 2.1', sample_udfs=smp_udfs)


def genotyping_info(session):
    art_udfs = ['Number of Calls (This Run)']
    smp_udfs = ['Number of Calls (Best Run)']
    return step_info(session, 'QuantStudio Data Import EG 2.0', sample_udfs=smp_udfs, output_udfs=art_udfs,
                     container_type='384 wells plate')
