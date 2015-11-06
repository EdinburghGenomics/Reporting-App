__author__ = 'mwham'
import argparse
import tornado.wsgi
import tornado.httpserver
import tornado.ioloop
import flask as fl


DEBUG = False
app = fl.Flask(__name__)
app.config.from_object(__name__)


@app.route('/')
def main_page():
    return fl.render_template('main.html')


@app.route('/project/<project>/')
def report_project(project):
    return fl.render_template('project_overview.html', project=project, num_points=0)


@app.route('/run_id/<run_id>/')
def report_run(run_id):
    # data = _fetch_data_points(run_id=run_id)
    return fl.render_template('run_overview.html', run_id=run_id, num_points=0)  # data['_meta']['total'])


@app.route('/<dataset_type>/<dataset>/demultiplexing')
def project_demultiplexing(dataset_type, dataset):
    return fl.render_template('demultiplexing_report.html', dataset_type=dataset_type, dataset=dataset)


def _join(*parts):
    return ''.join(parts)


if __name__ == '__main__':

    p = argparse.ArgumentParser()
    p.add_argument('-p', '--port', type=int, help='port to run the Flask app on')
    args = p.parse_args()

    http_server = tornado.httpserver.HTTPServer(tornado.wsgi.WSGIContainer(app))
    http_server.listen(args.port)
    tornado.ioloop.IOLoop.instance().start()
