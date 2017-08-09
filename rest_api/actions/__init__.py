
from flask import jsonify
from rest_api.actions.reviews import start_run_review


function_mapping = {
    'review_run': start_run_review
}


def perform_action(endpoint, app):
    data = function_mapping[endpoint]()
    ret_dict = {app.config['META']: {'total': len(data)}, app.config['ITEMS']: data}
    return jsonify(ret_dict)
