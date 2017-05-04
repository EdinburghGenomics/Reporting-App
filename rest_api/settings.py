from config import schema, rest_config as cfg

DOMAIN = {

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

    'run_elements': {
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
    },

    'analysis_driver_stages': {
        'url': 'analysis_driver_stages',
        'item_title': 'analysis_driver_stage',
        'id_field': 'stage_id',
        'schema': schema['analysis_driver_stages']
    }
}

MONGO_HOST = cfg['db_host']
MONGO_PORT = cfg['db_port']
MONGO_DBNAME = cfg['db_name']
ITEMS = 'data'

XML = False

PAGINATION = True
PAGINATION_LIMIT = 100000

X_DOMAINS = cfg['x_domains']
X_HEADERS = ['Authorization']

RESOURCE_METHODS = ['GET', 'POST', 'DELETE']
ITEM_METHODS = ['GET', 'PUT', 'PATCH', 'DELETE']

CACHE_CONTROL = 'max-age=20'
CACHE_EXPIRES = 20

DATE_FORMAT = '%d_%m_%Y_%H:%M:%S'

# disable default behaviour
RETURN_MEDIA_AS_BASE64_STRING = False

# return media as URL instead
RETURN_MEDIA_AS_URL = True

# set up the desired media endpoint
MEDIA_ENDPOINT = 'media'

if cfg.get('url_prefix') and cfg.get('api_version'):
    URL_PREFIX = cfg['url_prefix']
    API_VERSION = cfg['api_version']
