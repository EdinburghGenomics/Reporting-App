__author__ = 'mwham'
import eve
import flask
import flask_cors
from config import rest_config as cfg, schema


def endpoint(route):
    return '/%s/%s/%s' % (settings['URL_PREFIX'], settings['API_VERSION'], route)


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
    'ITEM_METHODS': ['GET', 'PUT', 'PATCH', 'DELETE']
}

from rest_api import aggregation


app = eve.Eve(settings=settings)
flask_cors.CORS(app)
# flask_cors.CORS(
#     app,
#     resources='%s/%s/*' % (settings['URL_PREFIX'], settings['API_VERSION']),
#     origins='http://localhost:5000'
# )

def _embedding(request_args):
    return flask.json.loads(request_args.get('embedded', '{}'))


def aggregate_embedded_run_elements(request, payload):
    input_json = flask.json.loads(payload.data.decode('utf-8'))
    if _embedding(request.args).get('run_elements') == 1:
        payload.data = aggregation.server_side.aggregate_lanes(input_json)


def embed_run_elements_into_samples(request, payload):
    input_json = flask.json.loads(payload.data.decode('utf-8'))
    if _embedding(request.args).get('run_elements') == 1:
        payload.data = aggregation.server_side.aggregate_samples(input_json)


def run_element_basic_aggregation(request, payload):
    input_json = flask.json.loads(payload.data.decode('utf-8'))
    payload.data = aggregation.server_side.run_element_basic_aggregation(input_json)


def format_json(resource, request, payload):
    payload.data = flask.json.dumps(flask.json.loads(payload.data.decode('utf-8')), indent=4)


app.on_post_GET += format_json
app.on_post_GET_samples += embed_run_elements_into_samples
app.on_post_GET_run_elements += run_element_basic_aggregation
app.on_post_GET_lanes += aggregate_embedded_run_elements


@app.route(endpoint('aggregate/run_by_lane/<run_id>'))
def aggregate_by_lane(run_id):
    return aggregation.database_side.aggregate(
        'run_elements',
        aggregation.database_side.queries.run_elements_by_lane(run_id, flask.request.args)
    )


@app.route(endpoint('aggregate/list_runs'))
def list_runs():
    return aggregation.database_side.aggregate(
        'run_elements',
        aggregation.database_side.queries.run_ids,
        list_field='_id'
    )


@app.route(endpoint('aggregate/list_projects'))
def list_projects():
    return aggregation.database_side.aggregate(
        'samples',
        aggregation.database_side.queries.project_ids,
        list_field='_id'
    )


@app.route(endpoint('aggregate/list_lanes/<collection>/<run_id>'))
def list_lanes(collection, run_id):
    return aggregation.database_side.aggregate(
        collection,
        aggregation.database_side.queries.run_lanes(run_id),
        list_field='_id'
    )


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
