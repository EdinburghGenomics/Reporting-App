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


def _query_api(url):
    return json.loads(requests.get(url).content.decode('utf-8'))


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
    return fl.render_template('runs.html', api_url=rest_query('runs'), cols=col_mappings['runs'])


@app.route('/runs/<run_id>')
def report_run(run_id):
    lanes = _distinct_values(
        'lane_number',
        _query_api(rest_query('lanes', where={'run_id': run_id}))['data']
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
        'api_url': rest_query('lanes', where={'run_id': run_id}, embedded={'run_elements': 1}),
        'cols': col_mappings['lane_aggregation']
    }

    return fl.render_template(
        'run_report.html',
        run_id=run_id,
        aggregations=[lane_aggregation],
        demultiplexing_tables=demultiplexing_tables,
        unexpected_barcode_tables=unexpected_barcode_tables
    )


@app.route('/runs/<run_id>/<filename>')
def serve_fastqc_report(run_id, filename):
    if '..' in filename or filename.startswith('/'):
        fl.abort(404)
    return fl.send_file(os.path.join(os.path.dirname(__file__), 'static', 'runs', run_id, filename))


@app.route('/projects/')
def project_reports():
    return fl.render_template('runs.html', api_url=rest_query('projects'), cols=col_mappings['projects'])


@app.route('/projects/<project>')
def report_project(project):
    return fl.render_template(
        'project_report.html',

        project=project,
        table={
            'title': 'Project report for ' + project,
            'name': project + '_report',
            'api_url': rest_query('samples', where={'project': project}, embedded={'run_elements': 1}),
            'cols': col_mappings['samples']
        }
    )


def main():
    if cfg['tornado']:
        import tornado.wsgi
        import tornado.httpserver
        import tornado.ioloop

        app.debug = cfg['debug']
        http_server = tornado.httpserver.HTTPServer(tornado.wsgi.WSGIContainer(app))
        http_server.listen(cfg['port'])
        tornado.ioloop.IOLoop.instance().start()

    else:
        app.run('localhost', cfg['port'], debug=cfg['debug'])


if __name__ == '__main__':
    main()
