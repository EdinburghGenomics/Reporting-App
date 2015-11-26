__author__ = 'mwham'
from flask import json
from config import schema
from operator import itemgetter
import statistics


def _sum(elements, param):
    s = 0
    for e in elements:
        s += e.get(param, 0)
    return s


def _avg(elements, param):
    return sum((e[param] for e in elements)) / len(elements)


def _percentage(element, num, denom):
    if not element[denom]:
        return None
    return (element[num] / element[denom]) * 100


def run_element_basic_aggregation(input_json, sortquery):
    for run_element in input_json['data']:
        aggregate_single_run_element(run_element)
    return json.dumps(order_json(input_json, sortquery), indent=4)


def aggregate_samples(input_json, sortquery):
    for sample in input_json['data']:
        embedded_run_elements = sample.get('run_elements', [])
        aggregated_run_element = {}
        for val_to_sum in ['bases_r1', 'bases_r2', 'q30_bases_r1', 'q30_bases_r2', 'total_reads',
                           'passing_filter_reads']:
            aggregated_run_element[val_to_sum] = _sum(embedded_run_elements, val_to_sum)
        aggregated_run_element['run_ids'] = ', '.join(set([e['run_id'] for e in embedded_run_elements]))
        aggregate_single_run_element(aggregated_run_element)
        sample.update(aggregated_run_element)

        sample['pc_mapped_reads'] = _percentage(sample, 'mapped_reads', 'bam_file_reads')
        sample['pc_properly_mapped_reads'] = _percentage(sample, 'properly_mapped_reads', 'bam_file_reads')
        sample['pc_duplicate_reads'] = _percentage(sample, 'duplicate_reads', 'bam_file_reads')
        del sample['run_elements']

    return json.dumps(order_json(input_json, sortquery), indent=4)


def aggregate_lanes(input_json, sortquery):
    for lane in input_json['data']:
        embedded_run_elements = lane.get('run_elements', [])
        aggregated_run_element = {}
        for val_to_sum in ['bases_r1', 'bases_r2', 'q30_bases_r1', 'q30_bases_r2', 'total_reads',
                           'passing_filter_reads']:
            aggregated_run_element[val_to_sum] = _sum(embedded_run_elements, val_to_sum)
        aggregated_run_element['run_ids'] = ', '.join(set([e['run_id'] for e in embedded_run_elements]))
        aggregate_single_run_element(aggregated_run_element)
        lane.update(aggregated_run_element)

        pass_filters = [e['passing_filter_reads'] for e in embedded_run_elements]
        lane['cv'] = statistics.stdev(pass_filters) / statistics.mean(pass_filters)

    return json.dumps(order_json(input_json, sortquery), indent=4)


def aggregate_single_run_element(e):
    e['pc_pass_filter'] = _percentage(e, 'passing_filter_reads', 'total_reads')
    e['pc_q30_r1'] = _percentage(e, 'q30_bases_r1', 'bases_r1')
    e['pc_q30_r2'] = _percentage(e, 'q30_bases_r2', 'bases_r2')
    e['pc_q30'] = (e['q30_bases_r1'] + e['q30_bases_r2']) / (e['bases_r1'] + e['bases_r2']) * 100
    e['yield_in_gb'] = (e['bases_r1'] + e['bases_r2']) / 1000000000


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
