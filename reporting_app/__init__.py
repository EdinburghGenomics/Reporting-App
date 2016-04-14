import flask as fl
import os.path
from reporting_app.util import query_api, rest_query, datatable_cfg, tab_set_cfg
from config import reporting_app_config as cfg

app = fl.Flask(__name__)


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
    lanes = sorted(set(e['lane_number'] for e in query_api('lanes', where={'run_id': run_id})))

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
        procs=query_api(
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
    sample = query_api('samples', where={'sample_id': sample_id}, embedded={'analysis_driver_procs': 1})[0]

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
