__author__ = 'mwham'
import argparse
import flask as fl
import pymongo


DEBUG = False

app = fl.Flask(__name__)
app.config.from_object(__name__)
cli = pymongo.MongoClient('localhost', 4998)
rest_api_base = 'http://localhost:4999/api/0.1'


def rest_url(extension):
    return rest_api_base + '/' + extension


@app.route('/')
def main_page():
    return fl.render_template('main.html')


@app.route('/reports/')
def reports():
    return fl.render_template('reports.html')


@app.route('/reports/runs/')
def run_reports():
    runs = set(x['run_id'] for x in cli['test_db']['run_elements'].find(projection={'run_id': True}))
    return fl.render_template('runs.html', runs=runs)


@app.route('/reports/runs/<run_id>')
def report_run(run_id):
    return fl.render_template(
        'run_report.html',
        run_id=run_id,

        datatables=[
            {
                'title': 'Demultiplexing',
                'name': 'demultiplexing',
                'api_url': rest_url('run_elements?where={"run_id":"%s"}' % run_id),
                'cols': (
                    ('lane', 'Lane'),
                    ('barcode', 'Barcode'),
                    ('project', 'Project'),
                    ('library_id', 'Library ID'),
                    ('sample_id', 'Sample ID'),
                    ('pc_pass_filter', '% Pass-filter'),
                    ('passing_filter_reads', 'Passing-filter reads'),
                    ('yield_in_gb', 'Yield (Gb)'),
                    ('pc_q30_r1', '% Q30 R1'),
                    ('pc_q30_r2', '% Q30 R2')
                )
            },
            {
                'title': 'Unexpected Barcodes',
                'name': 'unexpected_barcodes',
                'api_url': rest_url('unexpected_barcodes?where={"run_id":"%s"}' % run_id),
                'cols': (
                    ('lane', 'Lane'),
                    ('barcode', 'Barcode'),
                    ('passing_filter_reads', 'Passing-filter reads'),
                    ('pc_reads_in_lane', '% Reads in lane')
                )
            }
        ]
    )


@app.route('/reports/projects/')
def project_reports():
    projects = set(x['project'] for x in cli['test_db']['samples'].find(projection={'project': True}))
    return fl.render_template('projects.html', projects=projects)


@app.route('/reports/projects/<project>')
def report_project(project):
    samples = set(x['sample_id'] for x in cli['test_db']['samples'].find(filter={'project': project}, projection={'sample_id': True}))
    print(samples)

    return fl.render_template(
        'project_report.html',

        project=project,
        datatables=[
            {
                'title': project,
                'name': project,
                'api_url': rest_url('samples?where={"project":"%s"}' % project),
                'cols': (
                    ('sample_id', 'Sample ID'),
                    ('library_id', 'Library ID'),
                    ('user_sample_id', 'User sample ID'),
                    ('yield_in_gb', 'Yield (Gb)'),
                    ('initial_reads', 'Initial reads'),
                    ('passing_filter_reads', 'Passing-filter reads'),
                    ('nb_mapped_reads', '# mapped reads'),
                    ('pc_mapped_reads', '% mapped reads'),
                    ('nb_properly_mapped_reads', '# properly mapped reads'),
                    ('pc_properly_mapped_reads', '% properly mapped reads'),
                    ('nb_duplicate_reads', '# duplicate reads'),
                    ('pc_duplicate_reads', '% duplicate reads'),
                    ('median_coverage', 'Median coverage'),
                    ('pc_callable', '% callable'),
                    ('pc_q30_r1', '% Q30 R1'),
                    ('pc_q30_r2', '% Q30 R2')
                )
            }
        ]
    )


def _join(*parts):
    return ''.join(parts)


if __name__ == '__main__':

    p = argparse.ArgumentParser()
    p.add_argument('-p', '--port', type=int, help='port to run the Flask app on')
    p.add_argument('-d', '--debug', action='store_true', help='run the app in debug mode')
    p.add_argument(
        '-t',
        '--tornado',
        action='store_true',
        help='whether to use Tornado\'s http server and wsgi container for external access'
    )
    args = p.parse_args()

    if args.tornado:
        import tornado.wsgi
        import tornado.httpserver
        import tornado.ioloop

        http_server = tornado.httpserver.HTTPServer(tornado.wsgi.WSGIContainer(app))
        http_server.listen(args.port)
        tornado.ioloop.IOLoop.instance().start()

    else:
        app.run('localhost', 5000, debug=True)
