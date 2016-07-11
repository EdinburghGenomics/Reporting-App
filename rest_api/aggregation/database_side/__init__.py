import pymongo
from json import loads
from bson.json_util import dumps
from flask import jsonify, request
from datetime import datetime
from eve.utils import parse_request
from eve.auth import requires_auth
from eve.methods.get import _pagination_links, _meta_links
from rest_api import app
from config import rest_config as cfg
from . import queries
from ..server_side import post_processing as pp


cli = pymongo.MongoClient(cfg['db_host'], cfg['db_port'])
db = cli[cfg['db_name']]


def aggregate(endpoint, base_pipeline, post_processing=None):
    before = datetime.now()
    collection = db[endpoint]
    pipeline = queries.resolve_pipeline(endpoint, base_pipeline)
    app.logger.debug(pipeline)
    data = list(collection.aggregate(pipeline))
    total_items = len(data)
    if post_processing:
        for p in post_processing:
            data = p(data)

    ret_dict = {}
    page_number = int(request.args.get(app.config['QUERY_PAGE'], '0'))
    page_size = int(request.args.get(app.config['QUERY_MAX_RESULTS'], '0'))
    if page_number and page_size:
        data = data[page_size * (page_number - 1): page_size * page_number]
        req = parse_request(endpoint)
        ret_dict[app.config['META']] = _meta_links(req, total_items),
        ret_dict[app.config['LINKS']] = _pagination_links(endpoint, req, total_items)
    else:
        ret_dict[app.config['META']] = {'total': total_items}

    ret_dict[app.config['ITEMS']] = data
    j = jsonify(loads(dumps(ret_dict)))  # cast ObjectIDs to dicts
    after = datetime.now()
    app.logger.info('Aggregated from %s in %s', endpoint, after - before)
    return j


def aggregate_endpoint(route):
    if app.config.get('URL_PREFIX') and app.config.get('API_VERSION'):
        return '/%s/%s/aggregate/%s' % (app.config['URL_PREFIX'], app.config['API_VERSION'], route)
    return '/aggregate/' + route  # Apache adds url prefix instead


@app.route(aggregate_endpoint('run_elements_by_lane'))
@requires_auth('home')
def aggregate_by_lane():
    return aggregate('run_elements', queries.run_elements_group_by_lane)


@app.route(aggregate_endpoint('all_runs'))
@requires_auth('home')
def run_info():
    return aggregate(
        'runs',
        queries.sequencing_run_information,
        post_processing=[pp.cast_to_sets('project_ids', 'review_statuses', 'useable_statuses')]
    )


@app.route(aggregate_endpoint('run_elements'))
@requires_auth('home')
def demultiplexing():
    return aggregate('run_elements', queries.demultiplexing)


@app.route(aggregate_endpoint('samples'))
@requires_auth('home')
def sample():
    return aggregate(
        'samples',
        queries.sample,
        post_processing=[pp.cast_to_sets('run_ids')]
    )


@app.route(aggregate_endpoint('projects'))
@requires_auth('home')
def project_info():
    return aggregate('projects', queries.project_info, post_processing=[pp.date_to_string('_created')])
