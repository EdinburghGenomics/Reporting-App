from flask import jsonify, request
import flask_cors
import pymongo
from bson.json_util import dumps
from json import loads
from rest_api import app
from eve.utils import parse_request
from eve.methods.get import _pagination_links, _meta_links
from config import rest_config as cfg
from . import queries
from ..server_side import post_processing as pp

from datetime import datetime


cli = pymongo.MongoClient(cfg['db_host'], cfg['db_port'])
db = cli[cfg['db_name']]


def aggregate(endpoint, base_pipeline, post_processing=None):
    before = datetime.now()
    collection = db[endpoint]
    pipeline = queries.resolve_pipeline(endpoint, base_pipeline)
    app.logger.debug(pipeline)
    cursor = collection.aggregate(pipeline)
    agg = list(cursor)
    print(agg)
    if post_processing:
        for p in post_processing:
            agg = p(agg)

    # total_items = collection.count(loads(request.args.get('match', '{}')))
    total_items = len(agg)
    page_number=int(request.args.get('page', '1'))
    page_size=int(request.args.get('max_results', '50'))
    pagg = agg[page_size * (page_number - 1): page_size * (page_number)]
    req = parse_request(endpoint)

    ret_dict = {
        app.config['ITEMS']: pagg,
        '_meta': _meta_links(req, total_items),
        '_links': _pagination_links(endpoint, req, total_items)
    }
    j = jsonify(loads(dumps(ret_dict)))
    after = datetime.now()
    app.logger.info('Aggregated from %s with pipeline. Time taken: %s', endpoint, after - before)
    return j


def aggregate_endpoint(route):
    return '/%s/%s/aggregate/%s' % (app.config['URL_PREFIX'], app.config['API_VERSION'], route)


flask_cors.CORS(app)

@app.route(aggregate_endpoint('run_elements_by_lane'))
def aggregate_by_lane():
    return aggregate('run_elements', queries.run_elements_group_by_lane)


@app.route(aggregate_endpoint('all_runs'))
def run_info():
    return aggregate(
        'runs',
        queries.sequencing_run_information,
        post_processing=[pp.cast_to_sets('project_ids', 'review_statuses', 'useable_statuses')]
    )


@app.route(aggregate_endpoint('run_elements'))
def demultiplexing():
    return aggregate('run_elements', queries.demultiplexing)


@app.route(aggregate_endpoint('samples'))
def sample():
    return aggregate(
        'samples',
        queries.sample,
        post_processing=[pp.cast_to_sets('run_ids')]
    )


@app.route(aggregate_endpoint('projects'))
def project_info():
    return aggregate('projects', queries.project_info, post_processing=[pp.date_to_string('_created')])
