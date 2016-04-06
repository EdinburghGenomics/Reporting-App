from flask import jsonify, request
import flask_cors
import pymongo
from bson.json_util import dumps
from json import loads
from rest_api import settings
from config import rest_config as cfg
from . import queries
from ..server_side import post_processing as pp

from datetime import datetime


cli = pymongo.MongoClient(cfg['db_host'], cfg['db_port'])
db = cli[cfg['db_name']]


def aggregate(collection, base_pipeline, post_processing=None):
    pipeline = queries.resolve_pipeline(collection, base_pipeline)
    print(pipeline)
    cursor = db[collection].aggregate(pipeline)
    agg = list(cursor)

    if post_processing:
        for p in post_processing:
            agg = p(agg)

    ret_dict = {
        settings['ITEMS']: agg,
        '_meta': {'total': len(agg)}
    }
    return jsonify(loads(dumps(ret_dict)))


def endpoint(route):
    return '/%s/%s/%s' % (settings['URL_PREFIX'], settings['API_VERSION'], route)


def register_db_side_aggregation(app):
    flask_cors.CORS(app)

    @app.route(endpoint('aggregate/run_by_lane/<run_id>'))
    def aggregate_by_lane(run_id):
        return aggregate(
            'run_elements',
            queries.run_elements_by_lane(run_id, request.args.get('sort', 'lane'))
        )

    @app.route(endpoint('aggregate/all_runs'))
    def run_info():
        before = datetime.now()
        a = aggregate(
            'runs',
            queries.sequencing_run_information,
            post_processing=[pp.cast_to_sets('project_ids', 'review_statuses', 'useable_statuses')]
        )
        after = datetime.now()
        print('all_runs')
        print('started: ' + str(before))
        print('finished: ' + str(after))
        print('time taken: ' + str(after - before))
        return a

    @app.route(endpoint('aggregate/demultiplexing/<run_id>/<lane>'))
    def demultiplexing(run_id, lane):
        return aggregate(
            'run_elements',
            queries.demultiplexing(run_id, lane, sort_col=request.args.get('sort', 'sample_id'))
        )

    @app.route(endpoint('aggregate/samples'))
    def sample():
        return aggregate(
            'samples',
            queries.sample(),
            post_processing=[pp.cast_to_sets('run_ids')]
        )

    @app.route(endpoint('aggregate/all_runs_opt'))
    def sample_opt():
        before = datetime.now()
        a = aggregate(
            'runs',
            queries.sequencing_run_information_opt,
            post_processing=[
                pp.cast_to_sets('project_ids', 'review_statuses', 'useable_statuses'),
                # pp.most_recent_proc(db, )
            ]
        )
        after = datetime.now()
        print('all_runs_opt')
        print('started: ' + str(before))
        print('finished: ' + str(after))
        print('time taken: ' + str(after - before))
        return a
