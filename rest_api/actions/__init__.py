import json

from flask import jsonify

from egcg_core import clarity
from pyclarity_lims.entities import Queue, Step
from requests.exceptions import HTTPError

from rest_api.aggregation.database_side import db
from rest_api.common import retrieve_args
from config import rest_config as cfg

lims_workflow_name = 'PostSeqLab EG 1.0 WF'
lims_stage_name = 'Sequencer Output Review EG 1.0 ST'


def run_review():
    kwargs = retrieve_args()
    sample_to_review = json.loads(kwargs.get('samples'))
    kwargs.get('username')
    kwargs.get('password')

    run_elements = {}
    print(sample_to_review)
    for sample_id in sample_to_review:
        run_elements[sample_id] = list(db['run_elements'].find({'sample_id': sample_id}))
    print(run_elements)
    try:
        lims = clarity.connection(new=True, username=kwargs.get('username'), password=kwargs.get('password'))
        # Test connection
        lims.get(lims.get_uri())
    except HTTPError:
        # TODO: return authentication error
        pass

    stage = clarity.get_workflow_stage(workflow_name=lims_workflow_name, stage_name=lims_stage_name)

    queue = Queue(lims, id=stage.step.id)
    samples_name_queued = set()
    artifacts_to_review = []

    # find all samples that are queued and to review
    artifacts = queue.artifacts
    for a in artifacts:
        assert len(a.samples) == 1
        if a.samples[0].name in sample_to_review:
            artifacts_to_review.append(a)
        samples_name_queued.add(a.samples[0].name)

    # find all samples that are to review but not queued
    sample_to_review_but_not_queued = set(sample_to_review).difference(samples_name_queued)
    if sample_to_review_but_not_queued:
        samples_tmp = clarity.get_list_of_samples(sample_names=list(sample_to_review_but_not_queued))
        artifacts = [s.artifact for s in samples_tmp]
        # Queue the artifacts there were not already there
        lims.route_artifacts(artifact_list=artifacts, stage_uri=stage.uri)
        artifacts_to_review.extend(artifacts)

    assert len(artifacts_to_review) == len(sample_to_review)
    print(artifacts_to_review)
    number_run_elements = [len(run_elements.get(a.samples[0].name)) for a in artifacts_to_review]
    # Create a new step from the queued artifacts
    # with the number of replicates that correspond to the number of run elements
    #s = Step.create(lims, protocol_step=stage.step, inputs=artifacts_to_review, replicates=number_run_elements)

    s = Step.create(lims, protocol_step=stage.step, inputs=artifacts_to_review)

    # Fill in the output artifact with information relevant for the review
    output_artifacts_to_upload = set()
    for sample_id in sample_to_review:
        re_number = 0
        for input, output in s.details.input_output_maps:
            iartifact = input.uri
            oartifact = output.uri
            # only deal with this one sample's output artifact
            if len(iartifact.samples) == 1 and iartifact.samples[0].name == sample_id:
                run_element = run_elements[sample_id][re_number]
                # push all the fields to the output artifact
                for field in ['run_element_id']:
                    oartifact.udf[field] = run_element.get(field)
                output_artifacts_to_upload.add(oartifact)
                re_number += 1
            # we've dealt with all the run elements
            assert len(run_elements[sample_id]) == re_number

    lims.put_batch(list(output_artifacts_to_upload))

    # Move from "Record detail" window to the "Next Step"
    s.advance()

    # Set the next step to complete
    for action in s.actions.next_actions:
        action['action'] = 'complete'
    s.actions.put()

    # build the returned json
    ret_json = {
        'url': cfg['clarity']['baseuri'] + '/clarity/work-complete/' + s.id.split('-')[1],
        'samples': run_elements
    }
    return ret_json


function_mapping = {
    'run_review': run_review
}


def perform_action(endpoint, app):
    data = function_mapping[endpoint]()
    ret_dict = {app.config['META']: {'total': len(data)}, app.config['ITEMS']: data}
    return jsonify(ret_dict)
