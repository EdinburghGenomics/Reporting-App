__author__ = 'mwham'
from flask import json
from config import schema
from operator import itemgetter
import statistics


def add(*args):
    return sum(args)


def total(param, elements):
    return sum(e[param] for e in elements)


def percentage(num, denom):
    if not denom:
        return None
    return multiply(divide(num, denom), 100)


def multiply(arg1, arg2):
    return arg1 * arg2


def divide(num, denom):
    return num / denom


def concatenate(elements, param):
    return ', '.join(sorted(set([e[param] for e in elements])))


def run_element_basic_aggregation(input_json, sortquery=None):
    for sample in input_json['data']:
        sample.update(_aggregate_run_element(sample))

    return json.dumps(order_json(input_json, sortquery), indent=4)


def _aggregate_run_element(element):
    return {
        'pc_pass_filter': multiply(divide(element['passing_filter_reads'], element['total_reads']), 100),
        'pc_q30_r1': multiply(divide(element['q30_bases_r1'], element['bases_r1']), 100),
        'pc_q30_r2': multiply(divide(element['q30_bases_r2'], element['bases_r2']), 100),
        'pc_q30': percentage(
            add(element['q30_bases_r1'], element['q30_bases_r2']),
            add(element['bases_r1'], element['bases_r2'])
        ),
        'yield_in_gb': divide(
            add(
                element['bases_r1'],
                element['bases_r2']
            ),
            1000000000
        )
    }


def aggregate_samples(input_json, sortquery=None):
    for sample in input_json['data']:
        sample.update(_aggregate_sample(sample, 'run_elements'))

    return json.dumps(order_json(input_json, sortquery), indent=4)


def _aggregate_sample(element, embedded_field):
    e = aggregate_embedded_run_elements(element[embedded_field])
    e.update(
        {
            'pc_mapped_reads': percentage(element['mapped_reads'], element['bam_file_reads']),
            'pc_properly_mapped_reads': percentage(element['properly_mapped_reads'], element['bam_file_reads']),
            'pc_duplicate_reads': percentage(element['duplicate_reads'], element['bam_file_reads'])
        }
    )
    del element[embedded_field]
    return e


def aggregate_embedded_run_elements(elements):
    for e in elements:
        _aggregate_run_element(e)
    return {
        'bases_r1': total('bases_r1', elements),
        'bases_r2': total('bases_r2', elements),
        'q30_bases_r1': total('q30_bases_r1', elements),
        'q30_bases_r2': total('q30_bases_r2', elements),
        'total_reads': total('total_reads', elements),
        'passing_filter_reads': total('passing_filter_reads', elements),
        'run_ids': concatenate(elements, 'run_id')
    }


def aggregate_lanes(input_json, sortquery=None):
    for lane in input_json['data']:
        lane.update(_aggregate_lane(lane, 'run_elements'))
    return json.dumps(order_json(input_json, sortquery), indent=4)


def _aggregate_lane(element, embedded_field):
    e = aggregate_embedded_run_elements(element[embedded_field])
    pass_filters = [e['passing_filter_reads'] for e in element[embedded_field]]
    e.update(
        {
            'cv': statistics.stdev(pass_filters) / statistics.mean(pass_filters)
        }
    )
    return e


def order_json(input_json, sortquery=None):
    resource = input_json['_links']['self']['title']
    if not sortquery:
        return input_json

    reverse = sortquery.startswith('-')
    sortcol = sortquery.lstrip('-')

    if sortcol not in schema[resource]:
        # do our own sorting, as sortcol refers to an aggregated field
        input_json['data'] = sorted(input_json['data'], key=lambda e: itemgetter(sortcol)(e), reverse=reverse)

    return input_json
