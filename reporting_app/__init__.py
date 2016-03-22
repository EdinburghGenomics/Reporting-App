__author__ = 'mwham'
import flask as fl
import os.path
import requests
from flask import json
from config import reporting_app_config as cfg, col_mappings


app = fl.Flask(__name__)


def rest_query(resource, **query_args):
    if not query_args:
        return cfg['rest_api'] + '/' + resource

    query = '?'
    query += '&'.join(['%s=%s' % (k, v) for k, v in query_args.items()]).replace(' ', '').replace('\'', '"')
    return cfg['rest_api'] + '/' + resource + query


def _query_api(resource, data_only=True, **query_args):
    url = rest_query(resource, **query_args)
    j = json.loads(requests.get(url).content.decode('utf-8'))
    if data_only:
        j = j['data']
    return j


def _distinct_values(val, input_json):
    return sorted(set(e[val] for e in input_json))


def _format_order(col_name, cols):
    if col_name.startswith('-'):
        direction = 'asc'
    else:
        direction = 'desc'

    return [
        [c['name'] for c in cols].index(col_name),
        direction
    ]


@app.route('/')
def main_page():
    return fl.render_template('reports.html')


@app.route('/runs/')
def run_reports():
    return fl.render_template(
        'runs.html',
        api_url=rest_query('runs', aggregate=True, embedded={'run_elements': 1, 'analysis_driver_procs': 1}),
        cols=col_mappings['runs']
    )


@app.route('/runs/<run_id>')
def report_run(run_id):
    lanes = _distinct_values(
        'lane_number',
        _query_api('lanes', where={'run_id': run_id})
    )
    demultiplexing_tables = [
        {
            'title': 'Lane ' + str(lane),
            'name': 'demultiplexing_lane_' + str(lane),
            'api_url': rest_query('run_elements', where={'run_id': run_id, 'lane': lane}),
            'cols': col_mappings['demultiplexing']
        }
        for lane in lanes
    ]

    unexpected_barcode_tables = [
        {
            'title': 'Lane ' + str(lane),
            'name': 'unexpected_barcodes_lane_' + str(lane),
            'api_url': rest_query('unexpected_barcodes', where={'run_id': run_id, 'lane': lane}),
            'cols': col_mappings['unexpected_barcodes'],
            'default_sort_col': _format_order('passing_filter_reads', col_mappings['unexpected_barcodes'])
        }
        for lane in lanes
    ]

    lane_aggregation = {
        'title': 'Aggregation per lane',
        'name': 'agg_per_lane',
        'api_url': rest_query('lanes', where={'run_id': run_id}, aggregate=True, embedded={'run_elements': 1}),
        'cols': col_mappings['lane_aggregation']
    }

    analysis_driver_procs = _query_api(
        'analysis_driver_procs',
        where={'dataset_type': 'run', 'dataset_name': run_id},
        sort='-start_date'
    )

    return fl.render_template(
        'run_report.html',
        run_id=run_id,
        aggregations=[lane_aggregation],
        demultiplexing_tables=demultiplexing_tables,
        unexpected_barcode_tables=unexpected_barcode_tables,
        analysis_driver_procs=analysis_driver_procs
    )


@app.route('/runs/<run_id>/<filename>')
def serve_fastqc_report(run_id, filename):
    if '..' in filename or filename.startswith('/'):
        fl.abort(404)
    return fl.send_file(os.path.join(os.path.dirname(__file__), 'static', 'runs', run_id, filename))


@app.route('/projects/')
def project_reports():
    return fl.render_template(
        'projects.html',
        api_url=rest_query('projects', aggregate=True, embedded={'samples': 1}),
        cols=col_mappings['projects']
    )


@app.route('/projects/<project_id>')
def report_project(project_id):
    return fl.render_template(
        'project_report.html',

        project=project_id,
        table={
            'title': 'Project report for ' + project_id,
            'name': project_id + '_report',
            'api_url': rest_query('samples', where={'project_id': project_id}, aggregate=True, embedded={'run_elements': 1}),
            'cols': col_mappings['samples']
        }
    )


@app.route('/samples/<sample_id>')
def report_sample(sample_id):
    return fl.render_template(
        'sample_report.html',

        sample = {
            'name': 'sample_' + str(sample_id),
            'api_url': rest_query('samples', where={'sample_id': sample_id}, aggregate=True, embedded={'run_elements': 1}),
            'cols': col_mappings['samples']
        },

        run_elements = {
            'name': 'run_elements_' + str(sample_id),
            'api_url': rest_query('run_elements', where={'sample_id': sample_id}, aggregate=True),
            'cols': col_mappings['demultiplexing']
        },

        sample_proc=_query_api(
            'samples',
            where={'sample_id': sample_id},
            embedded={'analysis_driver_procs': 1}
        )[0]
    )
