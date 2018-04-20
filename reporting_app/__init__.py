from os.path import join, dirname
from urllib.parse import quote, unquote
import datetime
import flask as fl
import flask_login
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
                construct_url('runs', max_results=10000),
                construct_url('lims/run_status'),
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
                construct_url('runs', where={'_created': {'$gte': time_ago.strftime(settings.DATE_FORMAT)}}, max_results=10000),
                construct_url('lims/run_status', createddate=time_ago.strftime(settings.DATE_FORMAT)),
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
            select={'style': 'os', 'blurable': True},
            review_url=construct_url('actions'),
            review_entity_field='sample_ids',
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
            api_url=construct_url('lanes', where={'run_id': run_id}),
            default_sort_col='lane_number',
            paging=False,
            searching=False,
            info=False,
            create_row='color_filter',
            select={'style': 'os', 'blurable': True},
            review_url=construct_url('actions'),
            review_entity_field='aggregated.sample_ids',
            buttons=['colvis', 'copy', 'pdf', 'runreview']
        ),
        tab_sets=[
            tab_set_cfg(
                'Demultiplexing reports per lane',
                [
                    datatable_cfg(
                        title='Demultiplexing lane ' + str(lane),
                        cols='demultiplexing',
                        api_url=construct_url('run_elements', where={'run_id': run_id, 'lane': lane}),
                        paging=False,
                        searching=False,
                        info=False,
                        create_row='color_filter',
                        select={'style': 'os', 'blurable': True},
                        review_url=construct_url('actions'),
                        review_entity_field='sample_id',
                        buttons=['colvis', 'copy', 'pdf', 'runreview']
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
            'All projects list',
            'projects',
            ajax_call={
                'func_name': 'merge_multi_sources',
                'api_urls': [
                    construct_url('projects', max_results=10000),
                    construct_url('lims/project_info', match={'project_status': 'all'}),
                ],
                'merge_on': 'project_id'
            }
        )
    )


@app.route('/samples/<view_type>')
@flask_login.login_required
def report_samples(view_type):
    year_ago = datetime.datetime.now() - datetime.timedelta(days=182)
    if view_type == 'all':
        ajax_call = {
            'func_name': 'merge_multi_sources_keep_first',
            'api_urls': [
                construct_url('samples', max_results=10000),
                construct_url('lims/sample_status', match={'project_status': 'all'}),
                construct_url('lims/sample_info', match={'project_status': 'all'})
            ],
            'merge_on': 'sample_id'
        }
        title = 'All samples'
    elif view_type == 'processing':

        ajax_call = {
            'func_name': 'merge_multi_sources_keep_first',
            'api_urls': [
                construct_url('samples', where={'aggregated.most_recent_proc.status': 'processing'},
                              max_results=10000),
                construct_url('lims/sample_status',
                              match={'createddate': year_ago.strftime(settings.DATE_FORMAT), 'project_status': 'open'}),
                construct_url('lims/sample_info',
                              match={'createddate': year_ago.strftime(settings.DATE_FORMAT), 'project_status': 'open'})
            ],
            'merge_on': 'sample_id'
        }
        title = 'Samples processing'
    elif view_type == 'toreview':
        ajax_call = {
            'func_name': 'merge_multi_sources_keep_first',
            'api_urls': [
                construct_url('samples',
                              where={'useable': 'not%20marked', 'aggregated.most_recent_proc.status': 'finished'},
                              max_results=10000),
                construct_url('lims/sample_status',
                              match={'createddate': year_ago.strftime(settings.DATE_FORMAT), 'project_status': 'open'}),
                construct_url('lims/sample_info',
                              match={'createddate': year_ago.strftime(settings.DATE_FORMAT), 'project_status': 'open'})
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
        review=True,
        table=datatable_cfg(
            title=title,
            cols='samples',
            ajax_call=ajax_call,
            select={'style': 'os', 'blurable': True},
            review_url=construct_url('actions'),
            review_entity_field='sample_id',
            buttons=['colvis', 'copy', 'pdf', 'samplereview']
        )
    )


@app.route('/projects/<project_ids>')
@flask_login.login_required
def report_project(project_ids):
    if project_ids == 'SGP':
        id_list = []
        for p in rest_api().get_documents('projects', all_pages=True):
            if p['project_id'].startswith('S'):
                id_list.append(p['project_id'])
    else:
        id_list = project_ids.split(',')

    if len(id_list) > 1:
        project_status_call = {
            'ajax_call': {
                'func_name': 'merge_multi_sources',
                'merge_on': 'project_id',
                'api_urls': [
                    construct_url('lims/project_status', match={'project_id': i, 'project_status': 'all'})
                    for i in id_list
                ]
            }
        }
        plate_status_call = {
            'ajax_call': {
                'func_name': 'merge_multi_sources',
                'merge_on': 'plate_id',
                'api_urls': [
                    construct_url('lims/plate_status', match={'project_id': i, 'project_status': 'all'})
                    for i in id_list
                ]
            }
        }
    else:
        project_status_call = {
            'api_url': construct_url('lims/project_status', match={'project_id': id_list[0], 'project_status': 'all'})
        }
        plate_status_call = {
            'api_url': construct_url('lims/plate_status', match={'project_id': id_list[0], 'project_status': 'all'})
        }

    procs = []
    bioinformatics_urls = []
    for i in id_list:
        x = rest_api().get_documents(
            'analysis_driver_procs',
            where={'dataset_type': 'project', 'dataset_name': i},
            embedded={'stages': 1},
            sort='-_created'
        )
        procs.extend(x)

        bioinformatics_urls += [
            construct_url('samples', where={'project_id': i}, max_results=10000),
            construct_url('lims/sample_status', match={'project_id': i, 'project_status': 'all'}),
            construct_url('lims/sample_info', match={'project_id': i, 'project_status': 'all'})
        ]

    return render_template(
        'project_report.html',
        'Project report for ' + project_ids,
        review=True,
        tables=[
            datatable_cfg(
                'Project Status for ' + project_ids,
                'project_status',
                paging=False,
                searching=False,
                info=False,
                **project_status_call
            ),
            datatable_cfg(
                'Plate Status for ' + project_ids,
                'plate_status',
                paging=False,
                searching=False,
                info=False,
                default_sort_col='plate_id',
                **plate_status_call
            ),
            datatable_cfg(
                'Bioinformatics report for ' + project_ids,
                'samples',
                ajax_call={
                    'func_name': 'merge_multi_sources',
                    'api_urls': bioinformatics_urls,
                    'merge_on': 'sample_id'
                },
                fixed_header=True,
                select={'style': 'os', 'blurable': True},
                review_url=construct_url('actions'),
                review_entity_field='sample_id',
                buttons=['colvis', 'copy', 'pdf', 'samplereview']
            )
        ],
        procs=procs
    )


@app.route('/sample/<sample_id>')
@flask_login.login_required
def report_sample(sample_id):
    return render_template(
        'sample_report.html',
        sample_id + ' Sample Report',
        review=True,
        tables=[
            datatable_cfg(
                'Bioinformatics report for ' + sample_id,
                'samples',
                api_url=None,
                ajax_call={
                    'func_name': 'merge_multi_sources',
                    'api_urls': [
                        construct_url('samples', where={'sample_id': sample_id}),
                        construct_url('lims/sample_status', match={'sample_id': sample_id, 'project_status': 'all'}),
                        construct_url('lims/sample_info', match={'sample_id': sample_id, 'project_status': 'all'})
                    ],
                    'merge_on': 'sample_id'
                },
                paging=False,
                searching=False,
                info=False,
                select={'style': 'os', 'blurable': True},
                review_url=construct_url('actions'),
                review_entity_field='sample_id',
                buttons=['colvis', 'copy', 'pdf', 'samplereview']
            ),
            datatable_cfg(
                'Run elements generated for ' + sample_id,
                'sample_run_elements',
                api_url=construct_url('run_elements', where={'sample_id': sample_id}, max_results=1000),
                paging=False,
                searching=False,
                info=False,
                create_row='color_filter'
            )
        ],
        sample_statuses=rest_api().get_document(
            'lims/status/sample_status',
            detailed=True,
            match={'sample_id': sample_id, 'project_status': 'all'}
        ),
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
        api_url=construct_url('run_elements', max_results=1000000),
        ajax_token=get_token()
    )


@app.route('/project_status', defaults={'prj_status': 'open'})
@app.route('/project_status/<prj_status>')
@flask_login.login_required
def project_status_reports(prj_status):
    # FIXME: Remove this ugly html generation when the page status becomes more stable
    from config import project_status as project_status_cfg
    table = '<table class="table"><th>Status</th> <th>Completed Steps</th> <th>Queued in Steps</th>'
    for sample_status in project_status_cfg.status_order:
        table += ''.join([
            '<tr>',
            '<th>' + sample_status + '</th>',
            '<td>' + ', '.join([
                                    step for step, st
                                    in project_status_cfg.step_completed_to_status.items()
                                    if st == sample_status
                                ]) + '</td>',
            '<td>' + ', '.join([
                                    step for step, st
                                    in project_status_cfg.step_queued_to_status.items()
                                    if st == sample_status
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
        prj_status.capitalize() + ' Project Status',
        description_html=collapse_description,
        table=datatable_cfg(
            'Status of ' + prj_status.capitalize() + ' Projects',
            'project_status',
            api_url=construct_url('lims/project_status', match={'project_status': prj_status}),
            state_save=True,
            fixed_header=True,
            table_foot='sum_row_per_column'
        )
    )
