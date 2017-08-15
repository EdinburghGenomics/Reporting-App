from flask import json
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.exceptions import abort

from rest_api.actions.reviews import start_run_review


function_mapping = {
    'run_review': start_run_review
}


def start_action(request):
    if request.form.get('action_type') in function_mapping:
        results = function_mapping[request.form.get('action_type')](request)
    else:
        abort(422, 'Unknown action type %s' % request.form.get('action_type'))
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
