from os.path import join, abspath, dirname
import eve
from eve.auth import requires_auth
import flask_cors
from werkzeug.exceptions import abort

import auth
from config import rest_config as cfg
from rest_api import actions
from rest_api.limsdb import lims_extract
from rest_api.aggregation import server_side
from rest_api.aggregation.database_side import aggregate, queries

app = eve.Eve(settings=join(dirname(abspath(__file__)), 'settings.py'), auth=auth.DualAuth)
app.secret_key = cfg['key'].encode()
flask_cors.CORS(app, supports_credentials=True, allow_headers=('Authorization',))

app.on_post_GET_samples += server_side.embed_run_elements_into_samples
app.on_post_GET_run_elements += server_side.run_element_basic_aggregation
app.on_post_GET_lanes += server_side.aggregate_embedded_run_elements
app.on_post_GET_runs += server_side.aggregate_embedded_run_elements_into_run
app.on_post_GET_projects += server_side.aggregate_embedded_sample_elements_into_project
app.on_pre_POST_actions += actions.start_action
app.on_post_POST_actions += actions.add_to_action

def _create_url_with(base, route):
    if app.config.get('URL_PREFIX') and app.config.get('API_VERSION'):
        return '/%s/%s/%s/%s' % (app.config['URL_PREFIX'], app.config['API_VERSION'], base, route)
    return '/' + base + '/' + route  # Apache adds url prefix instead


def _aggregate_endpoint(route):
    return _create_url_with('aggregate', route)


def _lims_endpoint(route):
    return _create_url_with('lims', route)


def _action_endpoint(route):
    return _create_url_with('actions', route)

@app.route(_aggregate_endpoint('run_elements_by_lane'))
@requires_auth('home')
def aggregate_by_lane():
    return aggregate('run_elements', queries.run_elements_group_by_lane, app)


@app.route(_aggregate_endpoint('all_runs'))
@requires_auth('home')
def run_info():
    return aggregate(
        'runs',
        queries.sequencing_run_information,
        app,
        post_processing=[server_side.post_processing.cast_to_sets('project_ids', 'review_statuses', 'useable_statuses')]
    )


@app.route(_aggregate_endpoint('run_elements'))
@requires_auth('home')
def demultiplexing():
    return aggregate(
        'run_elements',
        queries.demultiplexing,
        app
    )


@app.route(_aggregate_endpoint('samples'))
@requires_auth('home')
def sample():
    return aggregate(
        'samples',
        queries.sample,
        app,
        post_processing=[server_side.post_processing.cast_to_sets('run_ids')]
    )


@app.route(_aggregate_endpoint('projects'))
@requires_auth('home')
def project_info():
    return aggregate(
        'projects',
        queries.project_info,
        app,
        post_processing=[server_side.post_processing.date_to_string('_created')]
    )


@app.route(_lims_endpoint('status/<status_type>'))
@requires_auth('home')
def lims_status_info(status_type):
    return lims_extract(
        status_type,
        app
    )


@app.route(_lims_endpoint('samples'))
@requires_auth('home')
def lims_sample_info():
    return lims_extract(
        'sample_info',
        app
    )
