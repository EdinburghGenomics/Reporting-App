from os.path import join, abspath, dirname
import eve
from eve.auth import requires_auth
import flask_cors
import auth
from config import rest_config as cfg
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


def _aggregate_endpoint(route):
    if app.config.get('URL_PREFIX') and app.config.get('API_VERSION'):
        return '/%s/%s/aggregate/%s' % (app.config['URL_PREFIX'], app.config['API_VERSION'], route)
    return '/aggregate/' + route  # Apache adds url prefix instead


def _lims_endpoint(route):
    if app.config.get('URL_PREFIX') and app.config.get('API_VERSION'):
        return '/%s/%s/lims/%s' % (app.config['URL_PREFIX'], app.config['API_VERSION'], route)
    return '/lims/' + route  # Apache adds url prefix instead


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


@app.route(_lims_endpoint('project_status'))
@requires_auth('home')
def lims_project_info():
    return lims_extract(
        'project_status',
        app
    )
