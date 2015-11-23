__author__ = 'mwham'
from flask import jsonify
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
