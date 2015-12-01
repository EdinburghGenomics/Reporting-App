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
    return list(sorted(set([e[param] for e in elements])))


def run_element_basic_aggregation(input_json, sortquery=None):
    for sample in input_json['data']:
        sample.update(_aggregate_run_element(sample))

    return order_json(input_json, sortquery)


def _aggregate_run_element(element):
    return {
        'pc_pass_filter': percentage(element['passing_filter_reads'], element['total_reads']),
        'pc_q30_r1': percentage(element['q30_bases_r1'], element['bases_r1']),
        'pc_q30_r2': percentage(element['q30_bases_r2'], element['bases_r2']),
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

    return order_json(input_json, sortquery)


def _aggregate_sample(element, embedded_field):
    e = aggregate_embedded_run_elements(element[embedded_field])
    e.update(
        {
            'pc_pass_filter': percentage(e['passing_filter_reads'], e['total_reads']),
            'pc_q30_r1': percentage(e['q30_bases_r1'], e['bases_r1']),
            'pc_q30_r2': percentage(e['q30_bases_r2'], e['bases_r2']),
            'pc_q30': percentage(
                add(e['q30_bases_r1'], e['q30_bases_r2']),
                add(e['bases_r1'], e['bases_r2'])
            ),
            'yield_in_gb': divide(
                add(
                    e['bases_r1'],
                    e['bases_r2']
                ),
                1000000000
            ),
            'pc_mapped_reads': percentage(element['mapped_reads'], element['bam_file_reads']),
            'pc_properly_mapped_reads': percentage(
                element['properly_mapped_reads'],
                element['bam_file_reads']
            ),
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
    return order_json(input_json, sortquery)


def _aggregate_lane(element, embedded_field):
    e = aggregate_embedded_run_elements(element[embedded_field])
    pass_filters = [e['passing_filter_reads'] for e in element[embedded_field]]
    e.update(
        {
            'pc_q30_r1': percentage(e['q30_bases_r1'], e['bases_r1']),
            'pc_q30_r2': percentage(e['q30_bases_r2'], e['bases_r2']),
            'pc_q30': percentage(
                add(e['q30_bases_r1'], e['q30_bases_r2']),
                add(e['bases_r1'], e['bases_r2'])),
            'pc_pass_filter': percentage(e['passing_filter_reads'], e['total_reads']),
            'yield_in_gb': divide(add(e['bases_r1'], e['bases_r2']), 1000000000),
            'cv': statistics.stdev(pass_filters) / statistics.mean(pass_filters)
        }
    )
    return e


def order_json(input_json, sortquery=None):
    if not sortquery:
        return json.dumps(input_json, indent=4)

    reverse = sortquery.startswith('-')
    sortcol = sortquery.lstrip('-')

    resource = input_json['_links']['self']['title']
    if sortcol not in schema[resource]:
        # sortcol refers to an aggregated field, so sort here
        input_json['data'] = sorted(input_json['data'], key=lambda e: itemgetter(sortcol)(e), reverse=reverse)

    return json.dumps(input_json, indent=4)
