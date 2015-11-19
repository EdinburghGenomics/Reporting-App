__author__ = 'mwham'
import eve
import pymongo
from flask import jsonify, request
import flask_cors
from config import rest_config as cfg, schema


settings = {
    'DOMAIN': {

        'run_elements': {  # demultiplexing reports
            'url': 'run_elements',
            'item_title': 'element',
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
            'schema': schema['samples']
        }
    },

    'MONGO_HOST': cfg['db_host'],
    'MONGO_PORT': cfg['db_port'],
    'MONGO_DBNAME': cfg['db_name'],
    'ITEMS': 'data',

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

cli = pymongo.MongoClient(cfg['db_host'], cfg['db_port'])
db = cli[cfg['db_name']]


def _endpoint(route):
    return '/%s/%s/%s' % (settings['URL_PREFIX'], settings['API_VERSION'], route)


def _format_order(query):
    if query.startswith('-'):
        return {query.lstrip('-'): -1}
    else:
        return {query: 1}


def _aggregate(collection, query, list_field=None):
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


@app.route(_endpoint('aggregate/run_by_lane/<run_id>'))
def aggregate_by_lane(run_id):
    return _aggregate(
        'run_elements',
        [
            {
                '$match': {
                    'run_id': run_id
                }
            },
            {
                '$project': {
                    'lane': '$lane',
                    'passing_filter_reads': '$passing_filter_reads',
                    'pc_pass_filter': '$pc_pass_filter',
                    'yield_in_gb': '$yield_in_gb',
                    'pc_q30': {'$divide': [{'$add': ['$pc_q30_r1', '$pc_q30_r2']}, 2]},
                    'pc_q30_r1': '$pc_q30_r1',
                    'pc_q30_r2': '$pc_q30_r2'}
            },
            {
                '$group': {
                    '_id': '$lane',
                    'passing_filter_reads': {'$sum': '$passing_filter_reads'},
                    'pc_pass_filter': {'$avg': '$pc_pass_filter'},
                    'yield_in_gb': {'$sum': '$yield_in_gb'},
                    'pc_q30': {'$avg': '$pc_q30'},
                    'pc_q30_r1': {'$avg': '$pc_q30_r1'},
                    'pc_q30_r2': {'$avg': '$pc_q30_r2'},
                    'stdev_pf': {'$stdDevSamp': '$passing_filter_reads'},
                    'avg_pf': {'$avg': '$passing_filter_reads'}
                }
            },
            {
                '$project': {
                    'lane': '$_id',
                    'passing_filter_reads': '$passing_filter_reads',
                    'pc_pass_filter': '$pc_pass_filter',
                    'yield_in_gb': '$yield_in_gb',
                    'pc_q30': '$pc_q30',
                    'pc_q30_r1': '$pc_q30_r1',
                    'pc_q30_r2': '$pc_q30_r2',
                    'cv': {'$divide': ['$stdev_pf', '$avg_pf']}
                }
            },
            {
                '$sort': _format_order(request.args.get('sort', 'lane'))
            }
        ]
    )


@app.route(_endpoint('aggregate/list_runs'))
def list_runs():
    return _aggregate(
        'run_elements',
        [
            {
                '$group': {'_id': '$run_id'}
            }
        ],
        list_field='_id'
    )


@app.route(_endpoint('aggregate/list_projects'))
def list_projects():
    return _aggregate(
        'samples',
        [
            {
                '$group': {'_id': '$project'}
            }
        ],
        list_field='_id'
    )


@app.route(_endpoint('aggregate/list_lanes/<collection>/<run_id>'))
def list_lanes(collection, run_id):
    return _aggregate(
        collection,
        [
            {
                '$match': {'run_id': run_id}
            },
            {
                '$group': {'_id': '$lane'}
            },
            {
                '$sort': {'_id': 1}
            }
        ],
        list_field='_id'
    )


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
        app.run('localhost', cfg['port'], debug=cfg['debug'])
