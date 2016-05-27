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
        table=datatable_cfg('All runs', 'runs', api_url=rest_query('aggregate/all_runs'))
    )


@app.route('/pipelines/<pipeline_type>/<view_type>')
def pipeline_report(pipeline_type, view_type):
    statuses = {
        'queued': ('reprocess', 'force_ready'),
        'processing': ('processing',),
        'finished': ('finished', 'failed'),
        'archived': ('deleted', 'aborted')
    }
    endpoints = {'samples': 'aggregate/samples', 'runs': 'aggregate/all_runs'}
    endpoint = endpoints[pipeline_type]

    if view_type == 'all':
        query = rest_query(endpoint)
    elif view_type in statuses:
        query = rest_query(endpoint, match={'$or': [{'proc_status': s} for s in statuses[view_type]]})
    else:
        fl.abort(404)
        return None

    return fl.render_template(
        'untabbed_datatables.html',
        table=datatable_cfg(
            util.capitalise(view_type) + ' ' + pipeline_type,
            pipeline_type,
            query
        )
    )


@app.route('/runs/<run_id>')
def report_run(run_id):
    lanes = sorted(set(e['lane_number'] for e in query_api('lanes', where={'run_id': run_id})))

    return fl.render_template(
        'run_report.html',
        title='Report for ' + run_id,
        lane_aggregation=datatable_cfg(
            title='Aggregation per lane',
            cols='lane_aggregation',
            api_url=rest_query('aggregate/run_elements_by_lane', match={'run_id': run_id}),
            default_sort_col='lane_number',
            paging=False,
            searching=False,
            info=False
        ),
        tab_sets=[
            tab_set_cfg(
                'Demultiplexing reports per lane',
                [
                    datatable_cfg(
                        title='Demultiplexing lane ' + str(lane),
                        cols='demultiplexing',
                        api_url=rest_query('aggregate/run_elements', match={'run_id': run_id, 'lane': lane}),
                        paging=False,
                        searching=False,
                        info=False
                    )
                    for lane in lanes
                ]
            ),
            tab_set_cfg(
                'Unexpected barcodes',
                [
                    datatable_cfg(
                        title='Unexpected barcodes lane ' + str(lane),
                        cols='unexpected_barcodes',
                        api_url=rest_query('unexpected_barcodes', where={'run_id': run_id, 'lane': lane}),
                        default_sort_col='passing_filter_reads',
                        paging=False,
                        searching=False,
                        info=False
                    )
                    for lane in lanes
                ]
            )
        ],
        procs=query_api(
            'analysis_driver_procs',
            where={'dataset_type': 'run', 'dataset_name': run_id},
            sort='-_created'
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
            api_url=rest_query('aggregate/projects')
        )
    )


@app.route('/projects/<project_id>')
def report_project(project_id):
    return fl.render_template(
        'untabbed_datatables.html',
        table=datatable_cfg(
            'Project report for ' + project_id,
            'samples',
            rest_query('aggregate/samples', match={'project_id': project_id})
        )
    )


@app.route('/samples/<sample_id>')
def report_sample(sample_id):
    sample = query_api('samples', where={'sample_id': sample_id})[0]

    return fl.render_template(
        'sample_report.html',
        title='Report for sample ' + sample_id,
        description='(From project %s)' % sample['project_id'],
        tables=[
            datatable_cfg(
                'Sample report',
                'samples',
                rest_query('aggregate/samples', match={'sample_id': sample_id}),
                paging=False,
                searching=False,
                info=False
            ),
            datatable_cfg(
                'Run elements report',
                'sample_run_elements',
                rest_query('aggregate/run_elements', match={'sample_id': sample_id}),
                paging=False,
                searching=False,
                info=False
            )
        ],
        procs=query_api(
            'analysis_driver_procs',
            where={'dataset_type': 'sample', 'dataset_name': sample_id},
            sort='-_created'
        )
    )


@app.route('/test/<sample_id>')
def report_test(sample_id):
    sample = query_api('samples', where={'sample_id': sample_id})[0]

    return fl.render_template(
        'test_report.html',
        title='Report for sample ' + sample_id,
        description='(From project %s)' % sample['project_id'],
        procs=query_api(
            'analysis_driver_procs',
            where={'dataset_type': 'sample', 'dataset_name': sample_id},
            sort='-_created'
        )
    )
