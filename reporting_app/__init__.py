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


def datatable_cfg(title, name, cols, api_url, paging=True, default_sort_col=None):
    if default_sort_col is None:
        default_sort_col = [0, 'desc']
    else:
        default_sort_col = _format_order(default_sort_col, col_mappings[cols])
    return {
        'title': title,
        'name': name,
        'cols': col_mappings[cols],
        'api_url': api_url,
        'default_sort_col': default_sort_col,
        'paging': paging
    }


def tab_set_cfg(title, name, tables):
    return {
        'title': title,
        'name': name,
        'tables': tables
    }


@app.route('/')
def main_page():
    return fl.render_template('main_page.html')


@app.route('/runs/')
def run_reports():
    return fl.render_template(
        'untabbed_datatables.html',
        table=datatable_cfg('All runs', 'all_runs', 'runs', api_url=rest_query('aggregate/all_runs'))
    )


@app.route('/pipelines/<pipeline_type>/<view_type>')
def pipeline_report(pipeline_type, view_type):
    statuses = {
        'queued': ('reprocess', 'force_ready'),
        'processing': ('processing',),
        'finished': ('finished', 'failed'),
        'archived': ('deleted', 'aborted'),
        'all': ('force_ready', 'processing', 'finished', 'failed', 'aborted', 'reprocess', 'deleted')
    }

    if view_type not in statuses:
        fl.abort(404)

    if pipeline_type == 'samples':
        endpoint = 'aggregate/samples'
    elif pipeline_type == 'runs':
        endpoint = 'aggregate/all_runs'
    else:
        fl.abort(404)
        return

    return fl.render_template(
        'untabbed_datatables.html',
        tables=[
            datatable_cfg(
                s[0].upper() + s[1:] + ' ' + pipeline_type,
                s + '_' + pipeline_type,
                pipeline_type,
                rest_query(endpoint, match={'proc_status': s}))
            for s in statuses[view_type]
        ]
    )


@app.route('/runs/<run_id>')
def report_run(run_id):
    lanes = _distinct_values(
        'lane_number',
        _query_api('lanes', where={'run_id': run_id})
    )

    return fl.render_template(
        'run_report.html',
        title='Report for ' + run_id,
        lane_aggregation=datatable_cfg(
            'Aggregation per lane',
            'agg_per_lane',
            'lane_aggregation',
            rest_query('aggregate/run_elements_by_lane', match={'run_id': run_id}),
            paging=False
        ),
        tab_sets=[
            tab_set_cfg(
                'Demultiplexing per lane',
                'demultiplexing',
                [
                    datatable_cfg(
                        'Lane ' + str(lane),
                        'demultiplexing_lane_' + str(lane),
                        'demultiplexing',
                        rest_query('aggregate/run_elements', match={'run_id': run_id, 'lane': lane})
                    )
                    for lane in lanes
                ]
            ),
            tab_set_cfg(
                'Unexpected barcodes',
                'unexpected_barcodes',
                [
                    datatable_cfg(
                        'Lane ' + str(lane),
                        'unexpected_barcode_lane_' + str(lane),
                        'unexpected_barcodes',
                        rest_query('unexpected_barcodes', where={'run_id': run_id, 'lane': lane}),
                        default_sort_col='passing_filter_reads'
                    )
                    for lane in lanes
                ]
            )
        ],
        procs=_query_api(
            'analysis_driver_procs',
            where={'dataset_type': 'run', 'dataset_name': run_id},
            sort='-start_date'
        )
    )


@app.route('/runs/<run_id>/<filename>')
def serve_fastqc_report(run_id, filename):
    if '..' in filename or filename.startswith('/'):
        fl.abort(404)
    return fl.send_file(os.path.join(os.path.dirname(__file__), 'static', 'runs', run_id, filename))


@app.route('/projects/')
def project_reports():
    return fl.render_template(
        'untabbed_datatables.html',
        table=datatable_cfg(
            'Project list',
            'projects',
            'projects',
            api_url=rest_query('aggregate/projects')
        )
    )


@app.route('/projects/<project_id>')
def report_project(project_id):
    return fl.render_template(
        'untabbed_datatables.html',
        title='Project report for ' + project_id,
        table=datatable_cfg(
            'Project report for ' + project_id,
            project_id + '_report',
            'samples',
            rest_query('aggregate/samples', match={'project_id': project_id})
        )
    )


@app.route('/samples/<sample_id>')
def report_sample(sample_id):
    sample = _query_api('samples', where={'sample_id': sample_id}, embedded={'analysis_driver_procs': 1})[0]

    return fl.render_template(
        'sample_report.html',
        title='Report for sample ' + sample_id,
        description='(From project %s)' % sample['project_id'],
        tables=[
            datatable_cfg(
                'Sample report',
                'sample_' + sample_id,
                'samples',
                rest_query('aggregate/samples', match={'sample_id': sample_id})
            ),
            datatable_cfg(
                'Run elements report',
                'run_elements_' + sample_id,
                'demultiplexing',
                rest_query('aggregate/run_elements', match={'sample_id': sample_id})
            )
        ],
        procs=sample['analysis_driver_procs']
    )
