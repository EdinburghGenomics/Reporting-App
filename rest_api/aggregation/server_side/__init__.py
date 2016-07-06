from flask import json
from config import schema
from operator import itemgetter
from .expressions import resolve
from . import queries, post_processing


def _aggregate_embedded_run_elements(element):
    return resolve(queries.aggregate_embedded_run_elements, element)


def _aggregate_sample(element):
    element.update(_aggregate_embedded_run_elements(element))
    element.update(resolve(queries.aggregate_sample, element))
    return element


def _aggregate_lane(element):
    element.update(_aggregate_embedded_run_elements(element))
    element.update(resolve(queries.aggregate_lane, element))
    return element


def _aggregate_run(element):
    element.update(_aggregate_embedded_run_elements(element))
    element.update(resolve(queries.aggregate_run, element))
    element.update(resolve(queries.aggregate_embedded_proc, element))
    return element


def _aggregate_project(element):
    return resolve(queries.aggregate_project, element)


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


def _aggregate_data(input_json, aggregate_func, sortquery=None, trim_run_elements=False):
    for element in input_json['data']:
        element.update(aggregate_func(element))
        if trim_run_elements:
            del element['run_elements']
    return _order_json(input_json, sortquery)


def _trigger_aggregation(request, response, aggregate_func, always_aggregate=False, trim_run_elements=False):
    input_json = json.loads(response.data.decode('utf-8'))
    # booleans get cast to strings in http requests
    if always_aggregate or request.args.get('aggregate') == 'True':
        response.data = _aggregate_data(
            input_json,
            aggregate_func,
            sortquery=request.args.get('sort'),
            trim_run_elements=trim_run_elements
        ).encode()


def aggregate_embedded_run_elements_into_run(request, response):
    _trigger_aggregation(request, response, _aggregate_run)


def aggregate_embedded_sample_elements_into_project(request, response):
    _trigger_aggregation(request, response, _aggregate_project)


def aggregate_embedded_run_elements(request, response):
    _trigger_aggregation(request, response, _aggregate_lane)


def embed_run_elements_into_samples(request, response):
    _trigger_aggregation(request, response, _aggregate_sample, trim_run_elements=True)


def run_element_basic_aggregation(request, response):
    _trigger_aggregation(request, response, _aggregate_run_element, always_aggregate=True)
