from flask import json
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.exceptions import abort
from rest_api.actions.automatic_review import AutomaticSampleReviewer, AutomaticRunReviewer
from rest_api.actions.reviews import RunReviewInitiator, SampleReviewInitiator


action_map = {
    'run_review': RunReviewInitiator,
    'sample_review': SampleReviewInitiator,
    'automatic_run_review': AutomaticRunReviewer,
    'automatic_sample_review': AutomaticSampleReviewer
}


def start_action(request):
    action_type = request.form.get('action_type')
    if action_type not in action_map:
        abort(422, 'Unknown action type %s' % request.form.get('action_type'))

    action = action_map[request.form.get('action_type')](request)
    results = action.perform_action()
    results['action_type'] = request.form.get('action_type')
    request.form = ImmutableMultiDict(results)


def add_to_action(request, response):
    """Add the payload of the post to the response data so it is available to the client"""
    input_json = json.loads(response.data.decode('utf-8'))
    input_json['data'] = request.form.to_dict()
    response.data = json.dumps(input_json, indent=4).encode()
