__author__ = 'mwham'
import flask as fl
import os.path
import requests
from flask import json
from config import reporting_app_config as cfg, col_mappings


app = fl.Flask(__name__)


def rest_url(extension):
    return cfg['rest_api'] + '/' + extension


def query_where(domain, **search_args):
    where_queries = []

    for k, v in search_args.items():
        q = '"%s":' % k
        if k == 'lane':
            q += str(v)
        else:
            q += '"%s"' % v
        where_queries.append(q)

    return rest_url(domain + '?where={' + ','.join(where_queries) + '}')


def _query_api(url):
    return json.loads(requests.get(url).content.decode('utf-8'))


@app.route('/')
def main_page():
    return fl.render_template('reports.html')


@app.route('/runs/')
def run_reports():
    runs = list(reversed(_query_api(rest_url('aggregate/list_runs'))['data']))
    return fl.render_template('runs.html', runs=runs)


@app.route('/runs/<run_id>')
def report_run(run_id):

    demultiplexing_lanes = _query_api(rest_url('aggregate/list_lanes/run_elements/' + run_id))['data']
    demultiplexing_tables = [
        {
            'title': 'Lane ' + str(lane),
            'name': 'demultiplexing_lane_' + str(lane),
            'api_url': query_where('run_elements', run_id=run_id, lane=lane),
            'cols': col_mappings['demultiplexing']
        }
        for lane in demultiplexing_lanes
    ]

    unexpected_barcode_lanes = _query_api(rest_url('aggregate/list_lanes/unexpected_barcodes/' + run_id))['data']
    unexpected_barcode_tables = [
        {
            'title': 'Lane ' + str(lane),
            'name': 'unexpected_barcodes_lane_' + str(lane),
            'api_url': query_where('unexpected_barcodes', run_id=run_id, lane=lane),
            'cols': col_mappings['unexpected_barcodes']
        }
        for lane in unexpected_barcode_lanes
    ]

    lane_aggregation = {
        'title': 'Aggregation per lane',
        'name': 'agg_per_lane',
        'api_url': rest_url('aggregate/run_by_lane/' + run_id),
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
        return None
    return fl.send_file(os.path.join(os.path.dirname(__file__), 'static', 'runs', run_id, filename))


@app.route('/projects/')
def project_reports():
    projects = _query_api(rest_url('aggregate/list_projects'))['data']
    return fl.render_template('projects.html', projects=projects)


@app.route('/projects/<project>')
def report_project(project):
    return fl.render_template(
        'project_report.html',

        project=project,
        table={
            'title': 'Project report for ' + project,
            'name': project + '_report',
            'api_url': query_where('samples', project=project),
            'cols': col_mappings['samples']
        }
    )


def _join(*parts):
    return ''.join(parts)


if __name__ == '__main__':

    if cfg['tornado']:
        import tornado.wsgi
        import tornado.httpserver
        import tornado.ioloop

        app.debug = cfg['debug']
        http_server = tornado.httpserver.HTTPServer(tornado.wsgi.WSGIContainer(app))
        http_server.listen(cfg['port'])
        tornado.ioloop.IOLoop.instance().start()

    else:
        app.run('localhost', cfg['port'], debug=True)
