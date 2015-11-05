__author__ = 'mwham'
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
    app.run('localhost', 5000)


x = {
    '_meta': {
        'max_results': 25,
        'total': 133,
        'page': 1
    },
    '_items': [
        {
            'run_id': '150723_test',
            '_links': {
                'self': {
                    'title': 'run_element',
                    'href': 'data_points/563383a8f4b2c64566ae3289'
                }
            },
            'lane': 1,
            '_updated': 'Fri, 30 Oct 2015 14:50:16 GMT',
            'sample_id': '10015AT0002_test',
            'library_id': 'LP600_test',
            'sample_project': '10015AT_test',
            '_id': '563383a8f4b2c64566ae3289',
            '_created': 'Fri, 30 Oct 2015 14:50:16 GMT',
            'payload': {
                'pc_of_Unexpected': '0.62%',
                'Barcode': 'CGCGCAGT',
                'pc_of_Lane': '0.01%',
                'Nb_of_Read': '664',
                'Lane': '6'
            },
            'barcode': 'TESTTEST',
            '_etag': '064dd42c751b9aa862c46907909360bfc2f08eb7',
            'report_type': 'demultiplexing'


        }
    ]
}
