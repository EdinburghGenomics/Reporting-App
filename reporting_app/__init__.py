__author__ = 'mwham'
import tornado.wsgi
import tornado.httpserver
import tornado.ioloop
import flask as fl
import requests

DEBUG = False
base_url = 'http://127.0.0.1:5002/'
eve_url = 'http://127.0.0.1:5002/'

app = fl.Flask(__name__)
app.config.from_object(__name__)


@app.route('/')
def main_page():
    return fl.render_template('main.html')


@app.route('/project/<project>/')
def report_project(project):
    data = _fetch_data_points(sample_project=project)
    return fl.render_template('project_overview.html', project=project, num_points=data['_meta']['total'])


@app.route('/run_id/<run_id>/')
def report_run(run_id):
    # data = _fetch_data_points(run_id=run_id)
    return fl.render_template('run_overview.html', run_id=run_id, num_points=0)# data['_meta']['total'])


@app.route('/<dataset_type>/<dataset>/demultiplexing')
def project_demultiplexing(dataset_type, dataset):
    return fl.render_template('demultiplexing_report.html', dataset_type=dataset_type, dataset=dataset)


def _fetch_data_points(**queries):
    query = _join(
        eve_url,
        'api/0.1/',
        'data_points?where=',
        '&'.join(('{type}=="{value}"'.format(type=k, value=v) for k, v in queries.items()))
    )
    print(query)
    return requests.get(query).json()


def _join(*parts):
    return ''.join(parts)


if __name__ == '__main__':
    print('setting up http server')
    http_server = tornado.httpserver.HTTPServer(tornado.wsgi.WSGIContainer(app))
    http_server.listen(5000)
    print('starting')
    tornado.ioloop.IOLoop.instance().start()
 
