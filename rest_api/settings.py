from config import schema, rest_config as cfg

DOMAIN = {
    endpoint: {
        'url': endpoint,
        'item_title': endpoint[:-1],
        'schema': schema[endpoint],
        'datasource': {
            'projection': {
                k: 1
                for k in ['_id', '_etag', '_updated', '_created', 'calculated', 'aggregated'] + list(schema[endpoint])
            }
        }
    }

    for endpoint in (
        'runs', 'lanes', 'run_elements', 'unexpected_barcodes', 'projects', 'samples', 'analysis_driver_procs',
        'analysis_driver_stages', 'actions'
    )

}

for endpoint, id_field in (
    ('lanes', 'lane_id'),
    ('run_elements', 'run_element_id'),
    ('samples', 'sample_id'),
    ('analysis_driver_procs', 'proc_id'),
    ('analysis_driver_stages', 'stage_id'),
    ('actions', 'action_id')
):
    DOMAIN[endpoint]['id_field'] = id_field


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


if cfg.get('url_prefix') and cfg.get('api_version'):
    URL_PREFIX = cfg['url_prefix']
    API_VERSION = cfg['api_version']
