__author__ = 'mwham'
from flask import json
from config import schema
from operator import itemgetter
from .expressions import resolve
from . import queries


def run_element_basic_aggregation(input_json, sortquery=None):
    for sample in input_json['data']:
        sample.update(_aggregate_run_element(sample))
    return _order_json(input_json, sortquery)


def aggregate_samples(input_json, sortquery=None):
    for sample in input_json['data']:
        sample.update(_aggregate_sample(sample, embedded_field='run_elements'))
    return _order_json(input_json, sortquery)


def aggregate_lanes(input_json, sortquery=None):
    for lane in input_json['data']:
        lane.update(_aggregate_lane(lane, 'run_elements'))
    return _order_json(input_json, sortquery)


def _aggregate_embedded_run_elements(element, embedded_field):
    return resolve(queries.aggregate_embedded_run_elements, element, embedded_field)


def _aggregate_sample(element, embedded_field):
    element.update(_aggregate_embedded_run_elements(element, embedded_field))
    element.update(resolve(queries.aggregate_sample, element))
    del element[embedded_field]
    return element


def _aggregate_lane(element, embedded_field):
    element.update(_aggregate_embedded_run_elements(element, embedded_field))
    element.update(resolve(queries.aggregate_lane, element, embedded_field))
    return element


def _aggregate_run_element(element):
    return resolve(queries.aggregate_run_element, element)


def _order_json(input_json, sortquery=None):
    if not sortquery:
        return json.dumps(input_json, indent=4)

    reverse = sortquery.startswith('-')
    sortcol = sortquery.lstrip('-')

    resource = input_json['_links']['self']['title']
    if sortcol not in schema[resource]:
        # sortcol refers to an aggregated field, so sort here
        input_json['data'] = sorted(input_json['data'], key=lambda e: itemgetter(sortcol)(e), reverse=reverse)

    return json.dumps(input_json, indent=4)
