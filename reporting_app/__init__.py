from os.path import join, dirname
from urllib.parse import quote, unquote
import flask as fl
import flask_login
import auth
from reporting_app.util import datatable_cfg, tab_set_cfg, get_token
from config import reporting_app_config as cfg

app = fl.Flask(__name__)
app.secret_key = cfg['key'].encode()
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
version = open(join(dirname(dirname(__file__)), 'version.txt')).read()


def rest_api():
    return flask_login.current_user.comm


def render_template(template, title=None, **context):
    return fl.render_template(template, title=title, version=version, **context)


@login_manager.user_loader
def load_user(user_id):
    return auth.User.get(user_id)


@login_manager.unauthorized_handler
def unauthorised_handler():
    return fl.redirect('/login?redirect=' + quote(fl.request.full_path, safe=()))


@login_manager.token_loader
def load_token(token_hash):
    uid = auth.check_login_token(token_hash)
    if uid:
        return auth.User.get(uid)


@app.route('/')
@flask_login.login_required
def main_page():
    return render_template('main_page.html', 'Main Page')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if fl.request.method == 'GET':
        return render_template(
            'login.html',
            'Login',
            message='Welcome to the EGCG Reporting App. Log in here.',
            redirect=quote(fl.request.args.get('redirect', ''), safe=())
        )
    username = fl.request.form['username']
    redirect = fl.request.form['redirect']
    if auth.check_user_auth(username, fl.request.form['pw']):
        u = auth.User(username)
        flask_login.login_user(u, remember=True)
        app.logger.info("Logged in user '%s'", username)
        return fl.redirect(unquote(redirect))
    return render_template('login.html', 'Login', message='Bad login.')


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return render_template('login.html', 'Logout', message='Logged out.')


@app.route('/change_password', methods=['GET', 'POST'])
@flask_login.login_required
def change_password():
    if fl.request.method == 'GET':
        return render_template('change_password.html', 'Change Password')

    user_id = flask_login.current_user.username
    form = fl.request.form
    if auth.change_pw(user_id, form['old_pw'], form['new_pw']):
        return fl.redirect('/logout')
    return render_template('login.html', 'Login', message='Bad request.')


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

    title = util.capitalise(view_type) + ' ' + pipeline_type

    return render_template(
        'untabbed_datatables.html',
        title,
        table=datatable_cfg(title, pipeline_type, query)
    )


@app.route('/run/<run_id>')
@flask_login.login_required
def report_run(run_id):
    lanes = sorted(set(e['lane_number'] for e in rest_api().get_documents('lanes', where={'run_id': run_id})))

    return render_template(
        'run_report.html',
        title=run_id + ' Run Report',
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
    return fl.send_file(join(dirname(__file__), 'static', 'runs', run_id, filename))


@app.route('/projects/')
@flask_login.login_required
def project_reports():
    return render_template(
        'untabbed_datatables.html',
        'Projects',
        table=datatable_cfg(
            'Project list',
            'projects',
            api_url=rest_api().api_url('aggregate/projects')
        )
    )


@app.route('/projects/<project_id>')
@flask_login.login_required
def report_project(project_id):
    return render_template(
        'untabbed_datatables.html',
        project_id + ' Project Report',
        table=datatable_cfg(
            'Project report for ' + project_id,
            'samples',
            rest_api().api_url('aggregate/samples', match={'project_id': project_id})
        )
    )


@app.route('/sample/<sample_id>')
@flask_login.login_required
def report_sample(sample_id):
    sample = rest_api().get_document('samples', where={'sample_id': sample_id})

    return render_template(
        'sample_report.html',
        title=sample_id + ' Sample Report',
        tables=[
            datatable_cfg(
                'Bioinformatics report for '+sample_id,
                'samples',
                rest_api().api_url('aggregate/samples', match={'sample_id': sample_id}),
                paging=False,
                searching=False,
                info=False
            ),
            datatable_cfg(
                'Run elements generated for '+ sample_id,
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

@app.route('/charts')
@flask_login.login_required
def plotting_report():
    return render_template(
        'charts.html',
        api_url=rest_api().api_url('aggregate/run_elements', paginate=False),
        ajax_token = get_token()
    )

@app.route('/project_status/')
@flask_login.login_required
def project_status_reports():
    return render_template(
        'untabbed_datatables.html',
        'Project Status',
        description='This table shows the number of sample in different categories based on the workflow they completed',
        table=datatable_cfg(
            'Project Status',
            'project_status',
            api_url=rest_api().api_url('lims/project_status')
        )
    )

