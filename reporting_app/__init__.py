__author__ = 'mwham'
import flask as fl
import os.path
import pymongo
from config import reporting_app_config as cfg, rest_config, col_mappings


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


@app.route('/')
def main_page():
    return fl.render_template('reports.html')


@app.route('/runs/')
def run_reports():
    runs = set(x['run_id'] for x in cli['test_db']['run_elements'].find(projection={'run_id': True}))
    return fl.render_template('runs.html', runs=runs)


@app.route('/runs/<run_id>')
def report_run(run_id):
    demultiplexing_lanes = set(x['lane'] for x in cli['test_db']['run_elements'].find(projection={'lane': True}))

    unexpected_barcode_lanes = set(x['lane'] for x in cli['test_db']['unexpected_barcodes'].find(projection={'lane': True}))

    demultiplexing_tables = []
    unexpected_barcode_tables = []
    for lane in demultiplexing_lanes:
        demultiplexing_tables.append(
            {
                'title': 'Demultiplexing data for lane ' + str(lane),
                'name': 'demultiplexing_lane_' + str(lane),
                'api_url': query_where('run_elements', run_id=run_id, lane=lane),
                'cols': col_mappings['demultiplexing']
            }
        )
    for lane in unexpected_barcode_lanes:
        unexpected_barcode_tables.append(
            {
                'title': 'Unexpected barcodes for lane ' + str(lane),
                'name': 'unexpected_barcodes_lane_' + str(lane),
                'api_url': query_where('unexpected_barcodes', run_id=run_id, lane=lane),
                'cols': col_mappings['unexpected_barcodes']
            }
        )

    return fl.render_template(
        'run_report.html',
        run_id=run_id,
        tab_sets=(
            {
                'name': 'demultiplexing',
                'datatables': demultiplexing_tables
            },
            {
                'name': 'unexpected_barcodes',
                'datatables': unexpected_barcode_tables
            }
        )
    )


@app.route('/runs/<run_id>/<filename>')
def serve_fastqc_report(run_id, filename):
    if '..' in filename or filename.startswith('/'):
        fl.abort(404)
        return None
    return fl.send_file(os.path.join(os.path.dirname(__file__), 'static', 'runs', run_id, filename))


@app.route('/projects/')
def project_reports():
    projects = set(x['project'] for x in cli['test_db']['samples'].find(projection={'project': True}))
    return fl.render_template('projects.html', projects=projects)


@app.route('/projects/<project>')
def report_project(project):
    return fl.render_template(
        'project_report.html',

        project=project,
        tab_sets=(
            {
                'name': 'samples',
                'datatables': (
                    {
                        'title': project,
                        'name': project,
                        'api_url': query_where('samples', project=project),
                        'cols': col_mappings['samples']
                    },
                )
            },
        )
    )


def _join(*parts):
    return ''.join(parts)


if __name__ == '__main__':

    app.debug = cfg['debug']
    cli = pymongo.MongoClient(cfg['database'])

    if cfg['tornado']:
        import tornado.wsgi
        import tornado.httpserver
        import tornado.ioloop

        http_server = tornado.httpserver.HTTPServer(tornado.wsgi.WSGIContainer(app))
        http_server.listen(cfg['port'])
        tornado.ioloop.IOLoop.instance().start()

    else:
        app.run('localhost', cfg['port'])
