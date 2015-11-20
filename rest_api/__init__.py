__author__ = 'mwham'
import eve
import pymongo
from flask import jsonify, request, json
import flask_cors
from config import rest_config as cfg, schema


def endpoint(route):
    return '/%s/%s/%s' % (settings['URL_PREFIX'], settings['API_VERSION'], route)

from rest_api import aggregation


settings = {
    'DOMAIN': {

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

        'samples': {  # bcbio reports
            'url': 'samples',
            'item_title': 'sample',
            'embedded_fields': ['run_elements'],
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

app = eve.Eve(settings=settings)
flask_cors.CORS(app)
# flask_cors.CORS(
#     app,
#     resources='%s/%s/*' % (settings['URL_PREFIX'], settings['API_VERSION']),
#     origins='http://localhost:5000'
# )


def embed_run_elements_into_samples(request, payload):
    payload.data = aggregation.server_side.process_embedded_json(json.loads(payload.data.decode('utf-8')))


app.on_post_GET_samples += embed_run_elements_into_samples


cli = pymongo.MongoClient(cfg['db_host'], cfg['db_port'])
db = cli[cfg['db_name']]


def _aggregate(collection, query, list_field='_id'):
    cursor = db[collection].aggregate(query)
    if list_field:
        aggregation = sorted([x[list_field] for x in cursor['result']])
    else:
        aggregation = cursor['result']

    ret_dict = {
        settings['ITEMS']: aggregation,
        '_meta': {'total': len(aggregation)}
    }
    return jsonify(ret_dict)


@app.route(endpoint('aggregate/run_by_lane/<run_id>'))
def aggregate_by_lane(run_id):
    return _aggregate('run_elements', aggregation.database_side.run_elements_by_lane(run_id, request.args))


@app.route(endpoint('aggregate/list_runs'))
def list_runs():
    return _aggregate('run_elements', aggregation.database_side.run_ids)


@app.route(endpoint('aggregate/list_projects'))
def list_projects():
    return _aggregate('samples', aggregation.database_side.project_ids)


@app.route(endpoint('aggregate/list_lanes/<collection>/<run_id>'))
def list_lanes(collection, run_id):
    return _aggregate(collection, aggregation.database_side.run_lanes(run_id))


if __name__ == '__main__':
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
        app.run('localhost', cfg['port'], debug=True)
