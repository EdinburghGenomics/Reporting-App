__author__ = 'mwham'
from flask import jsonify, request
import flask_cors
import pymongo
from rest_api import settings
from config import rest_config as cfg
from . import queries


cli = pymongo.MongoClient(cfg['db_host'], cfg['db_port'])
db = cli[cfg['db_name']]


def aggregate(collection, query, list_field=None):
    cursor = db[collection].aggregate(query)
    if list_field:
        agg = sorted([x[list_field] for x in cursor['result']])
    else:
        agg = cursor['result']

    ret_dict = {
        settings['ITEMS']: agg,
        '_meta': {'total': len(agg)}
    }
    return jsonify(ret_dict)


def endpoint(route):
    return '/%s/%s/%s' % (settings['URL_PREFIX'], settings['API_VERSION'], route)


def register_db_side_aggregation(app):
    flask_cors.CORS(app)

    @app.route(endpoint('aggregate/run_by_lane/<run_id>'))
    def aggregate_by_lane(run_id):
        return aggregate(
            'run_elements',
            queries.run_elements_by_lane(run_id, request.args)
        )

    @app.route(endpoint('aggregate/list_runs'))
    def list_runs():
        return aggregate(
            'run_elements',
            queries.run_ids,
            list_field='_id'
        )

    @app.route(endpoint('aggregate/list_projects'))
    def list_projects():
        return aggregate(
            'samples',
            queries.project_ids,
            list_field='_id'
        )

    @app.route(endpoint('aggregate/list_lanes/<collection>/<run_id>'))
    def list_lanes(collection, run_id):
        return aggregate(
            collection,
            queries.run_lanes(run_id),
            list_field='_id'
        )
