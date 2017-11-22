import pymongo
from json import loads
from bson.json_util import dumps
from flask import jsonify, request
from datetime import datetime
from eve.utils import parse_request
from eve.methods.get import _pagination_links, _meta_links
from config import rest_config as cfg
from . import queries

cli = pymongo.MongoClient(cfg['db_host'], cfg['db_port'])
db = cli[cfg['db_name']]


def _aggregate(endpoint, base_pipeline, request_args, post_processing=None):
    collection = db[endpoint]
    pipeline = queries.resolve_pipeline(endpoint, base_pipeline, request_args)
    data = list(collection.aggregate(pipeline, allowDiskUse=True))
    if post_processing:
        for p in post_processing:
            data = p(data)
    return data


def aggregate(endpoint, base_pipeline, app, post_processing=None):
    before = datetime.now()
    data = _aggregate(endpoint, base_pipeline, request.args, post_processing)
    total_items = len(data)
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
