__author__ = 'mwham'
from flask import json


def process_embedded_json(input_json):
    for element in input_json['data']:
        try:
            total = sum((r['total_reads'] for r in element['run_elements']))
            element['yield_in_gb'] = total / 1000000000
        except KeyError:
            pass

    return json.dumps(input_json)
