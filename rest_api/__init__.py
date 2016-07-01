import eve
import flask_cors
import auth
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

    'MONGO_HOST': cfg['db_host'],
    'MONGO_PORT': cfg['db_port'],
    'MONGO_DBNAME': cfg['db_name'],
    'ITEMS': 'data',

    'XML': False,

    'PAGINATION': True,
    'PAGINATION_LIMIT': 100000,

    'X_DOMAINS': cfg['x_domains'],
    'X_HEADERS': ['Authorization'],

    'URL_PREFIX': 'api',
    'API_VERSION': '0.1',

    'RESOURCE_METHODS': ['GET', 'POST', 'DELETE'],
    'ITEM_METHODS': ['GET', 'PUT', 'PATCH', 'DELETE'],

    'CACHE_CONTROL': 'max-age=20',
    'CACHE_EXPIRES': 20,

    'DATE_FORMAT': '%d_%m_%Y_%H:%M:%S'
}


app = eve.Eve(settings=settings, auth=auth.DualAuth)
app.secret_key = cfg['key'].encode()
flask_cors.CORS(app, supports_credentials=True, allow_headers=('Authorization',))

from rest_api import aggregation

app.on_post_GET_samples += aggregation.server_side.embed_run_elements_into_samples
app.on_post_GET_run_elements += aggregation.server_side.run_element_basic_aggregation
app.on_post_GET_lanes += aggregation.server_side.aggregate_embedded_run_elements
app.on_post_GET_runs += aggregation.server_side.aggregate_embedded_run_elements_into_run
app.on_post_GET_projects += aggregation.server_side.aggregate_embedded_sample_elements_into_project
