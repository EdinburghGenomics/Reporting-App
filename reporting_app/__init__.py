from os.path import join, dirname
from urllib.parse import quote, unquote
import datetime
import flask as fl
import flask_login
import base64

import auth
from reporting_app.util import datatable_cfg, tab_set_cfg, get_token
from config import reporting_app_config as cfg
from rest_api import settings

app = fl.Flask(__name__)
app.secret_key = cfg['key'].encode()
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
version = open(join(dirname(dirname(__file__)), 'version.txt')).read()


def construct_url(endpoint, **query_args):
    url = rest_api().api_url(endpoint)
    if query_args:
        url += '?' + '&'.join(['%s=%s' % (k, v) for k, v in query_args.items()])
    return url.replace('\'', '"')


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
    return render_template(
        'login.html',
        'Login',
        message='Bad login.',
        redirect=redirect
    )


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


@app.route('/runs/<view_type>')
@flask_login.login_required
def runs_report(view_type):
    if view_type == 'all':
        ajax_call = {
            'func_name': 'merge_multi_sources',
            'api_urls': [
                construct_url('aggregate/all_runs'),
                construct_url('lims/status/run_status'),
            ],
            'merge_on': 'run_id'
        }
    elif view_type in ['recent', 'current_year', 'year_to_date']:
        if view_type == 'recent':
            time_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        elif view_type == 'year_to_date':
            time_ago = datetime.datetime.now() - datetime.timedelta(days=365)
        elif view_type == 'current_year':
            y = datetime.datetime.now().year
            time_ago = datetime.datetime(year=y, month=1, day=1)
            view_type = str(y)
        ajax_call = {
            'func_name': 'merge_multi_sources',
            'api_urls': [
                construct_url('aggregate/all_runs', match={"_created": {"$gte": time_ago.strftime(settings.DATE_FORMAT)}}),
                construct_url('lims/status/run_status', createddate=time_ago.strftime(settings.DATE_FORMAT)),
            ],
            'merge_on': 'run_id'
        }
    else:
        fl.abort(404)
        return None
    title = util.capitalise(view_type).replace('_', ' ') + ' runs'

    return render_template(
        'untabbed_datatables.html',
        title,
        table=datatable_cfg(
            title=title,
            cols='runs',
            ajax_call=ajax_call,
            create_row='color_filter',
            fixed_header=True,
            select={'style':'os', 'blurable': True},
            run_review_url=construct_url('actions'),
            run_review_field='sample_ids',
            buttons=['colvis', 'copy', 'pdf', 'runreview']
        ),
        review=True
    )


@app.route('/run/<run_id>')
@flask_login.login_required
def report_run(run_id):
    lanes = sorted(set(e['lane_number'] for e in rest_api().get_documents('lanes', where={'run_id': run_id})))

    return render_template(
        'run_report.html',
        title=run_id + ' Run Report',
        review=True,
        lane_aggregation=datatable_cfg(
            title='Aggregation per lane',
            cols='lane_aggregation',
            api_url=construct_url('aggregate/run_elements_by_lane', match={'run_id': run_id}),
            default_sort_col='lane_number',
            paging=False,
            searching=False,
            info=False,
            create_row='color_filter',
            select = {'style': 'os', 'blurable': True},
            run_review_url = construct_url('actions'),
            run_review_field = 'sample_ids',
            buttons = ['colvis', 'copy', 'pdf', 'runreview']
        ),
        tab_sets=[
            tab_set_cfg(
                'Demultiplexing reports per lane',
                [
                    datatable_cfg(
                        title='Demultiplexing lane ' + str(lane),
                        cols='demultiplexing',
                        api_url=construct_url('aggregate/run_elements', match={'run_id': run_id, 'lane': lane}),
                        paging=False,
                        searching=False,
                        info=False,
                        create_row='color_filter',
                        select = {'style': 'os', 'blurable': True},
                        run_review_url = construct_url('actions'),
                        run_review_field = 'sample_id',
                        buttons = ['colvis', 'copy', 'pdf', 'runreview']
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
                        api_url=construct_url('unexpected_barcodes', where={'run_id': run_id, 'lane': lane}),
                        default_sort_col='passing_filter_reads',
                        paging=False,
                        searching=False,
                        info=False,
                        create_row='color_filter'
                    )
                    for lane in lanes
                ]
            )
        ],
        procs=rest_api().get_documents(
            'analysis_driver_procs',
            where={'dataset_type': 'run', 'dataset_name': run_id},
            embedded={'stages': 1},
            sort='-_created'
        )
    )

@app.route('/projects/')
@flask_login.login_required
def project_reports():
    return render_template(
        'untabbed_datatables.html',
        'Projects',
        table=datatable_cfg(
            'Project list',
            'projects',
            api_url=construct_url('aggregate/projects')
        )
    )


@app.route('/samples/<view_type>')
@flask_login.login_required
def report_samples(view_type):
    if view_type == 'all':
        ajax_call = {
            'func_name': 'merge_multi_sources_keep_first',
            'api_urls': [
                construct_url('aggregate/samples'),
                construct_url('lims/status/sample_status'),
                construct_url('lims/samples')
            ],
            'merge_on': 'sample_id'
        }
        title = 'All samples'
    elif view_type == 'toreview':
        three_month_ago = datetime.datetime.now() - datetime.timedelta(days=91)
        ajax_call = {
            'func_name': 'merge_multi_sources_keep_first',
            'api_urls': [
                construct_url('aggregate/samples', match={"useable": 'not%20marked', 'proc_status': 'finished'}),
                construct_url('lims/status/sample_status', match={'createddate': three_month_ago.strftime(settings.DATE_FORMAT)}),
                construct_url('lims/samples', match={'createddate': three_month_ago.strftime(settings.DATE_FORMAT)})
            ],
            'merge_on': 'sample_id'
        }
        title = 'Samples to review'
    else:
        fl.abort(404)
        return None

    return render_template(
        'untabbed_datatables.html',
        title,
        table=datatable_cfg(
            title=title,
            cols='samples',
            ajax_call=ajax_call
        )
    )


@app.route('/projects/<project_id>')
@flask_login.login_required
def report_project(project_id):
    return render_template(
        'untabbed_datatables.html',
        project_id + ' Project Report',
        tables=[
            datatable_cfg(
                'Project Status for ' + project_id,
                'project_status',
                api_url=construct_url('lims/status/project_status', match={'project_id': project_id}),
                paging=False,
                searching=False,
                info=False
            ),
            datatable_cfg(
                'Plate Status for ' + project_id,
                'plate_status',
                api_url=construct_url('lims/status/plate_status', match={'project_id': project_id}),
                paging=False,
                searching=False,
                info=False,
                default_sort_col='plate_id'
            ),
            datatable_cfg(
                'Bioinformatics report for ' + project_id,
                'samples',
                ajax_call={
                    'func_name': 'merge_multi_sources',
                    'api_urls': [
                        construct_url('aggregate/samples', match={'project_id': project_id}),
                        construct_url('lims/status/sample_status', match={'project_id': project_id}),
                        construct_url('lims/samples', match={'project_id': project_id})
                    ],
                    'merge_on': 'sample_id'
                },
                fixed_header=True
            )
        ]
    )


@app.route('/sample/<sample_id>')
@flask_login.login_required
def report_sample(sample_id):

    return render_template(
        'sample_report.html',

        title=sample_id + ' Sample Report',
        tables=[
            datatable_cfg(
                'Bioinformatics report for ' + sample_id,
                'samples',
                api_url=None,
                ajax_call={
                    'func_name': 'merge_multi_sources',
                    'api_urls': [
                        construct_url('aggregate/samples', match={'sample_id': sample_id}),
                        construct_url('lims/status/sample_status', match={'sample_id': sample_id}),
                        construct_url('lims/samples', match={'sample_id': sample_id})
                    ],
                    'merge_on': 'sample_id'
                },
                paging=False,
                searching=False,
                info=False
            ),
            datatable_cfg(
                'Run elements generated for ' + sample_id,
                'sample_run_elements',
                api_url=construct_url('aggregate/run_elements', match={'sample_id': sample_id}),
                paging=False,
                searching=False,
                info=False,
                create_row='color_filter'
            )
        ],
        sample_statuses=rest_api().get_document('lims/status/sample_status', detailed=True, match={'sample_id': sample_id}),
        lims_url=cfg['lims_url'],
        sample_id=sample_id,
        procs=rest_api().get_documents(
            'analysis_driver_procs',
            where={'dataset_type': 'sample', 'dataset_name': sample_id},
            embedded={'stages': 1},
            sort='-_created'
        )
    )


@app.route('/charts')
@flask_login.login_required
def plotting_report():
    return render_template(
        'charts.html',
        api_url=construct_url('aggregate/run_elements', paginate=False),
        ajax_token=get_token()
    )


@app.route('/project_status/')
@flask_login.login_required
def project_status_reports():
    # FIXME: Remove this ugly html generation when the page status becomes more stable
    from config import project_status as project_status_cfg
    table = '<table class="table"><th>Status</th> <th>Completed Steps</th> <th>Queued in Steps</th>'
    for status in project_status_cfg.status_order:
        table += ''.join([
            '<tr>',
            '<th>' + status + '</th>',
            '<td>' + ', '.join([
                                    step for step, st
                                    in project_status_cfg.step_completed_to_status.items()
                                    if st == status
                                ]) + '</td>',
            '<td>' + ', '.join([
                                    step for step, st
                                    in project_status_cfg.step_queued_to_status.items()
                                    if st == status
                                ]) + '</td>',
            '</tr>'
        ])
    table += '</table>'

    collapse_description = '''<button data-toggle="collapse" data-target="#description">Description</button>
<div id="description" class="collapse">
The project status table shows the number sample in each project based on the workflow they completed and the step
they're queued. the steps involved are described below.''' + table + '</div>'
    return render_template(
        'untabbed_datatables.html',
        'Project Status',
        description_html=collapse_description,
        table=datatable_cfg(
            'Project Status',
            'project_status',
            api_url=construct_url('lims/status/project_status'),
            fixed_header=True,
            table_foot='sum_row_per_column'
        )
    )


@app.route('/fastqc/<run_element_id>_<read>')
def send_fastq_html(run_element_id, read):
    if read == 'R1':
        report_key = 'fastqc_report_r1'
    elif read == 'R2':
        report_key = 'fastqc_report_r2'
    else:
        fl.abort(404)

    doc = rest_api().get_document('run_elements', where={'run_element_id':run_element_id}, projection={report_key:1})
    if doc and report_key in doc:
        return base64.b64decode(doc.get(report_key).get('file'))
    else:
        fl.abort(404)

if __name__ == "__main__":
    app.run()
