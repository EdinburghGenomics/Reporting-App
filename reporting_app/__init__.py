__author__ = 'mwham'
import argparse
import tornado.wsgi
import tornado.httpserver
import tornado.ioloop
import flask as fl
import pymongo


DEBUG = False

app = fl.Flask(__name__)
app.config.from_object(__name__)
cli = pymongo.MongoClient('localhost', 4998)
rest_api_base = 'http://localhost:4999/api/0.1'


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
    return fl.render_template('run_report.html', run_id=run_id)


@app.route('/reports/samples/')
def sample_reports():
    return fl.render_template('samples.html')


@app.route('/reports/samples/<sample_id>')
def project_demultiplexing(sample_id):
    return fl.render_template('sample_report.html', sample_id=sample_id)


def _join(*parts):
    return ''.join(parts)


if __name__ == '__main__':

    p = argparse.ArgumentParser()
    p.add_argument('-p', '--port', type=int, help='port to run the Flask app on')
    args = p.parse_args()

    http_server = tornado.httpserver.HTTPServer(tornado.wsgi.WSGIContainer(app))
    http_server.listen(args.port)
    tornado.ioloop.IOLoop.instance().start()
