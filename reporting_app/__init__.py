import os.path
import flask as fl
import flask_login
from itsdangerous import TimedSerializer
import auth
from config import reporting_app_config as cfg
from reporting_app.util import datatable_cfg, tab_set_cfg
from egcg_core.rest_communication import Communicator

app = fl.Flask(__name__)
app.secret_key = cfg['key'].encode()
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
_communicator = None


def rest_api():
    global _communicator
    if _communicator is None:
        _communicator = Communicator(auth.encode_string(flask_login.current_user.api_token), cfg['rest_api'])
    return _communicator


def generate_api_token(user_id):
    data = {}
    if user_id:
        data['token'] = user_id
    return TimedSerializer(app.secret_key).dumps(data)


@login_manager.user_loader
def load_user(user_id):
    return auth.User(user_id)


@login_manager.unauthorized_handler
def unauthorised_handler():
    return fl.redirect('/login')


@app.route('/')
@flask_login.login_required
def main_page():
    return fl.render_template('main_page.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if fl.request.method == 'GET':
        return fl.render_template('login.html')
    username = fl.request.form['username']
    if auth.match_passwords(username, fl.request.form['pw']):
        u = auth.User(username, api_token=generate_api_token(username))
        flask_login.login_user(u)
        return fl.redirect('/')
    return 'Bad login'


@app.route('/logout')
def logout():
    flask_login.current_user.erase_token()
    flask_login.logout_user()
    return 'Logged out'


@app.route('/change_password', methods=['GET', 'POST'])
@flask_login.login_required
def change_password():
    if fl.request.method == 'GET':
        return fl.render_template('change_password.html')

    user_id = flask_login.current_user.id
    form = fl.request.form
    if auth.match_passwords(user_id, form['old_pw']):
        auth.change_pw(user_id, form['old_pw'], form['new_pw'])
        return fl.redirect('/logout')
    return 'Bad request'


@app.route('/runs/')
@flask_login.login_required
def run_reports():
    return fl.render_template(
        'untabbed_datatables.html',
        table=datatable_cfg('All runs', 'runs', api_url=rest_api().api_url('aggregate/all_runs'))
    )


@app.route('/pipelines/<pipeline_type>/<view_type>')
@flask_login.login_required
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
        query = rest_api().api_url(endpoint)
    elif view_type in statuses:
        query = rest_api().api_url(endpoint, match={'$or': [{'proc_status': s} for s in statuses[view_type]]})
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
@flask_login.login_required
def report_run(run_id):
    lanes = sorted(set(e['lane_number'] for e in rest_api().get_documents('lanes', where={'run_id': run_id})))

    return fl.render_template(
        'run_report.html',
        title='Report for ' + run_id,
        lane_aggregation=datatable_cfg(
            title='Aggregation per lane',
            cols='lane_aggregation',
            api_url=rest_api().api_url('aggregate/run_elements_by_lane', match={'run_id': run_id}),
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
                        api_url=rest_api().api_url('aggregate/run_elements', match={'run_id': run_id, 'lane': lane}),
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
                        api_url=rest_api().api_url('unexpected_barcodes', where={'run_id': run_id, 'lane': lane}),
                        default_sort_col='passing_filter_reads',
                        paging=False,
                        searching=False,
                        info=False
                    )
                    for lane in lanes
                ]
            )
        ],
        procs=rest_api().get_documents(
            'analysis_driver_procs',
            where={'dataset_type': 'run', 'dataset_name': run_id},
            sort='-_created'
        )
    )


@app.route('/runs/<run_id>/<filename>')
@flask_login.login_required
def serve_fastqc_report(run_id, filename):
    if '..' in filename or filename.startswith('/'):
        fl.abort(404)
    return fl.send_file(os.path.join(os.path.dirname(__file__), 'static', 'runs', run_id, filename))


@app.route('/projects/')
@flask_login.login_required
def project_reports():
    return fl.render_template(
        'untabbed_datatables.html',
        table=datatable_cfg(
            'Project list',
            'projects',
            api_url=rest_api().api_url('aggregate/projects')
        )
    )


@app.route('/projects/<project_id>')
@flask_login.login_required
def report_project(project_id):
    return fl.render_template(
        'untabbed_datatables.html',
        table=datatable_cfg(
            'Project report for ' + project_id,
            'samples',
            rest_api().api_url('aggregate/samples', match={'project_id': project_id})
        )
    )


@app.route('/samples/<sample_id>')
@flask_login.login_required
def report_sample(sample_id):
    sample = rest_api().get_documents('samples', where={'sample_id': sample_id})[0]

    return fl.render_template(
        'sample_report.html',
        title='Report for sample ' + sample_id,
        description='(From project %s)' % sample['project_id'],
        tables=[
            datatable_cfg(
                'Sample report',
                'samples',
                rest_api().api_url('aggregate/samples', match={'sample_id': sample_id}),
                paging=False,
                searching=False,
                info=False
            ),
            datatable_cfg(
                'Run elements report',
                'sample_run_elements',
                rest_api().api_url('aggregate/run_elements', match={'sample_id': sample_id}),
                paging=False,
                searching=False,
                info=False
            )
        ],
        procs=rest_api().get_documents(
            'analysis_driver_procs',
            where={'dataset_type': 'sample', 'dataset_name': sample_id},
            sort='-_created'
        )
    )
