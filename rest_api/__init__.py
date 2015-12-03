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

        'samples': {  # bcbio reports
            'url': 'samples',
            'item_title': 'sample',
            'schema': schema['samples']
        }
    },
    'VALIDATE_FILTERS': True,

    'MONGO_HOST': cfg['db_host'],
    'MONGO_PORT': cfg['db_port'],
    'MONGO_DBNAME': cfg['db_name'],
    'ITEMS': 'data',

    'XML': False,

    'X_DOMAINS': cfg['x_domains'],

    'URL_PREFIX': 'api',
    'API_VERSION': '0.1',

    'RESOURCE_METHODS': ['GET', 'POST', 'DELETE'],
    'ITEM_METHODS': ['GET', 'PUT', 'PATCH', 'DELETE'],

    'CACHE_CONTROL': 'max-age=20',
    'CACHE_EXPIRES': 20
}

from rest_api import aggregation

app = eve.Eve(settings=settings)
if cfg.get('database_side_aggregation'):
    aggregation.database_side.register_db_side_aggregation(app)


def _from_query_string(request_args, query, json=True):
    if json:
        return flask.json.loads(request_args.get(query, '{}'))
    else:
        return request_args.get(query, None)


def aggregate_embedded_run_elements(request, response):
    input_json = flask.json.loads(response.data.decode('utf-8'))
    if _from_query_string(request.args, 'embedded').get('run_elements') == 1:
        response.data = aggregation.server_side.aggregate_lanes(
            input_json,
            sortquery=_from_query_string(request.args, 'sort', json=False)
        ).encode()


def embed_run_elements_into_samples(request, response):
    input_json = flask.json.loads(response.data.decode('utf-8'))
    if _from_query_string(request.args, 'embedded').get('run_elements') == 1:
        response.data = aggregation.server_side.aggregate_samples(
            input_json,
            sortquery=_from_query_string(request.args, 'sort', json=False)
        ).encode()


def run_element_basic_aggregation(request, response):
    input_json = flask.json.loads(response.data.decode('utf-8'))
    response.data = aggregation.server_side.run_element_basic_aggregation(
        input_json,
        sortquery=_from_query_string(request.args, 'sort', json=False)
    ).encode()


app.on_post_GET_samples += embed_run_elements_into_samples
app.on_post_GET_run_elements += run_element_basic_aggregation
app.on_post_GET_lanes += aggregate_embedded_run_elements


def main():
    """
    querying with Python syntax:
    curl -i -g 'http://host:port/things?where=sample_project=="this"'
    http://host:port/things?where=sample_project==%22this%22

    and MongoDB syntax:
    curl -i -g 'http://host:port/things?where={"sample_project":"this"}'
    http://host:port/things?where={%22sample_project%22:%22this%22}
    """
    if cfg['tornado']:
        import tornado.wsgi
        import tornado.httpserver
        import tornado.ioloop

        http_server = tornado.httpserver.HTTPServer(tornado.wsgi.WSGIContainer(app))
        http_server.listen(cfg['port'])
        tornado.ioloop.IOLoop.instance().start()

    else:
        app.run('localhost', cfg['port'], debug=cfg['debug'])


if __name__ == '__main__':
    main()
