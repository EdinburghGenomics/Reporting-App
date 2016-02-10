__author__ = 'mwham'
import eve
import flask
from config import rest_config as cfg, schema


settings = {
    'DOMAIN': {

        'runs': {
            'url': 'runs',
            'item_title': 'run',
            'schema': schema['runs']
        },

        'lanes': {
            'url': 'lanes',
            'item_title': 'lane',
            'id_field': 'lane_id',
            'schema': schema['lanes']
        },

        'run_elements': {  # demultiplexing reports
            'url': 'run_elements',
            'item_title': 'element',
            'id_field': 'run_element_id',
            'schema': schema['run_elements']
        },

        'unexpected_barcodes': {
            'url': 'unexpected_barcodes',
            'item_title': 'unexpected_barcode',
            'schema': schema['unexpected_barcodes']
        },

        'projects': {
            'url': 'projects',
            'item_title': 'project',
            'schema': schema['projects']
        },

        'samples': {
            'url': 'samples',
            'item_title': 'sample',
            'id_field': 'sample_id',
            'schema': schema['samples']
        },

        'analysis_driver_procs': {
            'url': 'analysis_driver_procs',
            'item_title': 'analysis_driver_proc',
            'id_field': 'proc_id',
            'schema': schema['analysis_driver_procs']
        }
    },
    'VALIDATE_FILTERS': True,

    'MONGO_HOST': cfg['db_host'],
    'MONGO_PORT': cfg['db_port'],
    'MONGO_DBNAME': cfg['db_name'],
    'ITEMS': 'data',

    'XML': False,

    'PAGINATION': True,
    'PAGINATION_LIMIT': 100000,

    'X_DOMAINS': cfg['x_domains'],

    'URL_PREFIX': 'api',
    'API_VERSION': '0.1',

    'RESOURCE_METHODS': ['GET', 'POST', 'DELETE'],
    'ITEM_METHODS': ['GET', 'PUT', 'PATCH', 'DELETE'],

    'CACHE_CONTROL': 'max-age=20',
    'CACHE_EXPIRES': 20,

    'DATE_FORMAT': '%d_%m_%Y_%H:%M:%S'
}

from rest_api import aggregation

app = eve.Eve(settings=settings)
# if cfg.get('database_side_aggregation'):
#     aggregation.database_side.register_db_side_aggregation(app)


def _from_query_string(request_args, query, json=False):
    if json:
        return flask.json.loads(request_args.get(query, '{}'))
    else:
        return request_args.get(query, None)


def _aggregation_enabled(request_args):
    return request_args.get('aggregate') == 'True'  # booleans get cast to strings in http requests


def aggregate_embedded_run_elements_into_run(request, response):
    input_json = flask.json.loads(response.data.decode('utf-8'))
    if _aggregation_enabled(request.args):
        response.data = aggregation.server_side.aggregate_run(
            input_json,
            sortquery=_from_query_string(request.args, 'sort')
        ).encode()


def aggregate_embedded_sample_elements_into_project(request, response):
    input_json = flask.json.loads(response.data.decode('utf-8'))
    if _aggregation_enabled(request.args):
        response.data = aggregation.server_side.aggregate_project(
            input_json,
            sortquery=_from_query_string(request.args, 'sort')
        ).encode()


def aggregate_embedded_run_elements(request, response):
    input_json = flask.json.loads(response.data.decode('utf-8'))
    if _aggregation_enabled(request.args):
        response.data = aggregation.server_side.aggregate_lanes(
            input_json,
            sortquery=_from_query_string(request.args, 'sort')
        ).encode()


def embed_run_elements_into_samples(request, response):
    input_json = flask.json.loads(response.data.decode('utf-8'))
    if _aggregation_enabled(request.args):
        response.data = aggregation.server_side.aggregate_samples(
            input_json,
            sortquery=_from_query_string(request.args, 'sort')
        ).encode()


def run_element_basic_aggregation(request, response):
    input_json = flask.json.loads(response.data.decode('utf-8'))
    response.data = aggregation.server_side.run_element_basic_aggregation(
        input_json,
        sortquery=_from_query_string(request.args, 'sort')
    ).encode()


app.on_post_GET_samples += embed_run_elements_into_samples
app.on_post_GET_run_elements += run_element_basic_aggregation
app.on_post_GET_lanes += aggregate_embedded_run_elements
app.on_post_GET_runs += aggregate_embedded_run_elements_into_run
app.on_post_GET_projects += aggregate_embedded_sample_elements_into_project


"""
querying with Python syntax:
curl -i -g 'http://host:port/things?where=sample_project=="this"'
http://host:port/things?where=sample_project==%22this%22

and MongoDB syntax:
curl -i -g 'http://host:port/things?where={"sample_project":"this"}'
http://host:port/things?where={%22sample_project%22:%22this%22}
"""
