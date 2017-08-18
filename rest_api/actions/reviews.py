import json

import datetime

import flask
from flask import current_app
from egcg_core import clarity
from pyclarity_lims.entities import Queue, Step
from requests.exceptions import HTTPError
from werkzeug.exceptions import abort

from rest_api import settings
from rest_api.actions.automatic_review import RunReviewer
from rest_api.aggregation.database_side import db
from config import rest_config as cfg

lims_workflow_name = 'PostSeqLab EG 1.0 WF'
lims_stage_name = 'Sequencer Output Review EG 1.0 ST'
fill_run_element_program_name = ''


def count_run_element(sample_id):
    return db['run_elements'].count({'sample_id': sample_id})


def start_run_review(request):
    # Get the information from the form's data
    sample_name_to_review = json.loads(request.form.get('samples'))
    username = request.form.get('username')
    password = request.form.get('password')

    # Get the number of run elements for each sample directly from the database.
    run_element_counts = {}
    for sample_id in sample_name_to_review:
        run_element_counts[sample_id] = count_run_element(sample_id)

    # Test the LIMS connection
    try:
        lims = clarity.connection(new=True, username=username, password=password, **cfg.get('clarity'))
        lims.get(lims.get_uri())
    except HTTPError:
        abort(401, 'Authentication in the LIMS (%s) failed' % cfg.get('clarity', {}).get('baseuri'))

    try:
        # Retrieve the samples from the LIMS
        samples_to_review = clarity.get_list_of_samples(sample_names=list(sample_name_to_review))
    except HTTPError:
        samples_to_review = []
    if len(samples_to_review) != len(sample_name_to_review):
        abort(409, 'Some of the sample to review were not found in the LIMS. %s samples requested %s samples found' % (
        len(sample_name_to_review), len(samples_to_review)))

    stage = clarity.get_workflow_stage(workflow_name=lims_workflow_name, stage_name=lims_stage_name)

    queue = Queue(lims, id=stage.step.id)
    samples_queued = set()
    artifacts_to_review = []

    # find all samples that are queued and to review
    artifacts = queue.artifacts
    for a in artifacts:
        if len(a.samples) != 1:
            abort(409, 'Artifact %s Queued on %s contains more than one sample' % (a.name, lims_stage_name))
        if a.samples[0].name in sample_name_to_review:
            artifacts_to_review.append(a)
        samples_queued.add(a.samples[0])

    # find all samples that are to review but not queued
    sample_to_review_but_not_queued = set(samples_to_review).difference(samples_queued)
    if sample_to_review_but_not_queued:
        artifacts = [s.artifact for s in sample_to_review_but_not_queued]
        # Queue the artifacts there were not already there
        lims.route_artifacts(artifact_list=artifacts, stage_uri=stage.uri)
        artifacts_to_review.extend(artifacts)

    if len(artifacts_to_review) != len(sample_name_to_review):
        abort(409, 'Could not find artifact for all samples.'
                   ' Make sure the sample name in the LIMS matches'
                   ' %s samples requested %s artifacts found' % (len(sample_name_to_review), len(artifacts_to_review)))
    number_run_elements = [run_element_counts.get(a.samples[0].name) for a in artifacts_to_review]
    # Create a new step from the queued artifacts
    # with the number of replicates that correspond to the number of run elements
    s = Step.create(lims, protocol_step=stage.step, inputs=artifacts_to_review, replicates=number_run_elements)

    if fill_run_element_program_name in s.program_names:
        s.trigger_program(fill_run_element_program_name)

    # build the returned json
    ret_json = {
        'action_id': 'lims_' + s.id,
        'started_by': username,
        'date_started': datetime.datetime.now().strftime(settings.DATE_FORMAT),
        'action_info': {
            'lims_step_name': lims_stage_name,
            'lims_url': cfg['clarity']['baseuri'] + '/clarity/work-details/' + s.id.split('-')[1],
            'samples': sample_name_to_review
        }
    }
    return ret_json




def automatic_run_review(request):
    start_time = datetime.datetime.now().strftime(settings.DATE_FORMAT)
    run_id = request.form.get('run_id')
    if hasattr(request.authorization, 'username'):
        username = request.authorization.username
    else:
        username = ''

    try:
        r = RunReviewer(run_id)
        r.push_review()
        return {
            'action_id': run_id + start_time,
            'date_started': start_time,
            'started_by': username,
            'date_finished': datetime.datetime.now().strftime(settings.DATE_FORMAT),
            'action_info': {
                'run_id': run_id
            }
        }
    except ValueError as e:
        abort(409, str(e))