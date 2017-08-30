from flask import json
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.exceptions import abort
from rest_api.actions.reviews import RunReviewInitiator, SampleReviewInitiator


initiators = {
    'run_review': RunReviewInitiator,
    'sample_review': SampleReviewInitiator
}


def start_action(request):
    action_type = request.form.get('action_type')
    if action_type not in initiators:
        abort(422, 'Unknown action type %s' % request.form.get('action_type'))

    initiator = initiators[request.form.get('action_type')](request)
    results = initiator.start_review()
    results['action_type'] = request.form.get('action_type')
    request.form = ImmutableMultiDict(results)


def add_to_action(request, response):
    """
    Add the content of the post request in the response
    so the data create by the action is available to the client
    """
    input_json = json.loads(response.data.decode('utf-8'))
    input_json['data'] = request.form.to_dict()
    response.data = json.dumps(input_json, indent=4).encode()
