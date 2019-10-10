from os.path import join, dirname
from urllib.parse import quote, unquote
import datetime
import flask as fl
import flask_login
import subprocess

import auth
from reporting_app import util
from reporting_app.util import resolve_cols
from rest_api import settings
from config import reporting_app_config as cfg, project_status as project_status_cfg

app = fl.Flask(__name__)
app.secret_key = cfg['key'].encode()
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
version = open(join(dirname(dirname(__file__)), 'version.txt')).read().strip()


def get_git_revision_short_hash():
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('utf-8').strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


git_commit = get_git_revision_short_hash()
if git_commit:
    # This should not appear once deployed in production.
    version = version + '-' + git_commit


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
    ajax_call = {'func_name': 'dt_merge_multi_sources', 'merge_on': 'run_id'}

    if view_type == 'all':
        ajax_call['api_urls'] = [
            util.construct_url('runs', max_results=10000),
            util.construct_url('lims/run_status'),
        ]

    elif view_type in ['recent', 'current_year', 'last_12_months']:
        if view_type == 'recent':
            time_ago = util.now() - datetime.timedelta(days=30)
        elif view_type == 'last_12_months':
            time_ago = util.now() - datetime.timedelta(days=365)
        elif view_type == 'current_year':
            y = util.now().year
            time_ago = datetime.datetime(year=y, month=1, day=1)
            view_type = str(y)

        ajax_call['api_urls'] = [
            util.construct_url('runs', where={'_created': {'$gte': time_ago.strftime(settings.DATE_FORMAT)}}, max_results=10000),
            util.construct_url('lims/run_status', createddate=time_ago.strftime(settings.DATE_FORMAT)),
        ]

    else:
        fl.abort(404)
        return None

    title = util.capitalise(view_type).replace('_', ' ') + ' Runs'

    return render_template(
        'untabbed_datatables.html',
        title,
        include_review_modal=True,
        table=util.datatable_cfg(
            title,
            'runs',
            ajax_call=ajax_call,
            create_row='color_filter',
            fixed_header=True,
            review={'entity_field': 'sample_ids', 'button_name': 'runreview'}
        )
    )


@app.route('/run/<run_id>')
@flask_login.login_required
def report_run(run_id):
    lanes = sorted(set(e['lane_number'] for e in rest_api().get_documents('lanes', where={'run_id': run_id})))

    return render_template(
        'run_report.html',
        run_id + ' Run Report',
        include_review_modal=True,
        lane_aggregation=util.datatable_cfg(
            'Aggregation per lane',
            'lane_aggregation',
            api_url=util.construct_url('lanes', where={'run_id': run_id}),
            default_sort_col='lane_number',
            minimal=True,
            create_row='color_filter',
            review={'entity_field': 'aggregated.sample_ids', 'button_name': 'runreview'}
        ),
        tab_sets=[
            util.tab_set_cfg(
                'Demultiplexing reports per lane',
                [
                    util.datatable_cfg(
                        'Demultiplexing lane ' + str(lane),
                        'demultiplexing',
                        api_url=util.construct_url('run_elements', where={'run_id': run_id, 'lane': lane}),
                        minimal=True,
                        create_row='color_filter',
                        review={'entity_field': 'sample_id', 'button_name': 'runreview'}
                    )
                    for lane in lanes
                ]
            ),
            util.tab_set_cfg(
                'Unexpected barcodes',
                [
                    util.datatable_cfg(
                        'Unexpected barcodes lane ' + str(lane),
                        'unexpected_barcodes',
                        api_url=util.construct_url('unexpected_barcodes', where={'run_id': run_id, 'lane': lane}),
                        default_sort_col='passing_filter_reads',
                        minimal=True,
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
        table=util.datatable_cfg(
            'All projects list',
            'projects',
            ajax_call={
                'func_name': 'dt_merge_multi_sources',
                'api_urls': [
                    util.construct_url('projects', max_results=10000),
                    util.construct_url('lims/project_info', match={'project_status': 'all'}),
                ],
                'merge_on': 'project_id'
            }
        )
    )


@app.route('/samples/<view_type>')
@flask_login.login_required
def report_samples(view_type):
    six_months_ago = util.now() - datetime.timedelta(days=182)
    ajax_call = {'func_name': 'dt_merge_multi_sources_keep_first', 'merge_on': 'sample_id'}

    if view_type == 'all':
        title = 'All samples'
        ajax_call['api_urls'] = [
            util.construct_url('samples', max_results=15000),
            util.construct_url('lims/sample_status', match={'project_status': 'all'}),
            util.construct_url('lims/sample_info', match={'project_status': 'all'})
        ]
    elif view_type == 'processing':
        title = 'Samples processing'
        ajax_call['api_urls'] = [
            util.construct_url('samples', where={'aggregated.most_recent_proc.status': 'processing'}, max_results=10000),
            util.construct_url('lims/sample_status', match={'createddate': six_months_ago.strftime(settings.DATE_FORMAT), 'project_status': 'open'}),
            util.construct_url('lims/sample_info', match={'createddate': six_months_ago.strftime(settings.DATE_FORMAT), 'project_status': 'open'})
        ]
    elif view_type == 'toreview':
        title = 'Samples to review'
        ajax_call['api_urls'] = [
            util.construct_url('samples', where={'useable': 'not%20marked', 'aggregated.most_recent_proc.status': 'finished'}, max_results=10000),
            util.construct_url('lims/sample_status', match={'createddate': six_months_ago.strftime(settings.DATE_FORMAT), 'project_status': 'open'}),
            util.construct_url('lims/sample_info', match={'createddate': six_months_ago.strftime(settings.DATE_FORMAT), 'project_status': 'open'})
        ]
    elif view_type == 'notprocessing':
        # Samples which have clean yield value populated, and have not started processing yet, or have a status of
        # reprocess, force_ready, resume or null.
        title = 'Samples not processing'
        ajax_call['api_urls'] = [
            util.construct_url('samples', where={"$and": [{"aggregated.clean_yield_in_gb": {"$exists": True, "$ne": None}},
                                                          {"$or": [
                                                            {"aggregated.most_recent_proc": None},
                                                            {"aggregated.most_recent_proc.status": None},
                                                            {"aggregated.most_recent_proc.status": "reprocess"},
                                                            {"aggregated.most_recent_proc.status": "force_ready"},
                                                            {"aggregated.most_recent_proc.status": "resume"}
                                                          ]}]}, max_results=10000),
            util.construct_url('lims/sample_status', match={'createddate': six_months_ago.strftime(settings.DATE_FORMAT), 'project_status': 'open'}),
            util.construct_url('lims/sample_info', match={'createddate': six_months_ago.strftime(settings.DATE_FORMAT), 'project_status': 'open'})
        ]
    else:
        fl.abort(404)
        return None

    return render_template(
        'untabbed_datatables.html',
        title,
        include_review_modal=True,
        table=util.datatable_cfg(
            title,
            'samples',
            ajax_call=ajax_call,
            review={'entity_field': 'sample_id', 'button_name': 'samplereview'},
            create_row='color_data_source'
        )
    )


@app.route('/projects/<project_ids>')
@flask_login.login_required
def report_project(project_ids):
    if project_ids == 'SGP':
        id_list = []
        for p in rest_api().get_documents('lims/project_info', match={'project_status': 'open'}):
            if p['project_id'].startswith('S'):
                id_list.append(p['project_id'])
    else:
        id_list = project_ids.split(',')

    if len(id_list) > 1:
        project_status_call = {
            'ajax_call': {
                'func_name': 'dt_merge_multi_sources',
                'merge_on': 'project_id',
                'api_urls': [
                    util.construct_url('lims/project_status', match={'project_id': i, 'project_status': 'all'})
                    for i in id_list
                ]
            }
        }
        plate_status_call = {
            'ajax_call': {
                'func_name': 'dt_merge_multi_sources',
                'merge_on': 'plate_id',
                'api_urls': [
                    util.construct_url('lims/plate_status', match={'project_id': i, 'project_status': 'all'})
                    for i in id_list
                ]
            }
        }
        library_info_call = {
            'ajax_call': {
                'func_name': 'dt_merge_multi_sources',
                'merge_on': 'library_id',
                'api_urls': [
                    util.construct_url('lims/library_info', match={'project_id': id_list[i]})
                    for i in id_list
                ]
            }
        }
        sample_qc_info_call = {
            'ajax_call': {
                'func_name': 'dt_merge_multi_sources',
                'merge_on': 'library_id',
                'api_urls': [
                    util.construct_url('lims/sample_qc_info', match={'project_id': id_list[i]})
                    for i in id_list
                ]
            }
        }
        genotyping_info_call = {
            'ajax_call': {
                'func_name': 'dt_merge_multi_sources',
                'merge_on': 'library_id',
                'api_urls': [
                    util.construct_url('lims/genotyping_info', match={'project_id': id_list[i]})
                    for i in id_list
                ]
            }
        }
    else:
        project_status_call = {
            'api_url': util.construct_url('lims/project_status', match={'project_id': id_list[0], 'project_status': 'all'})
        }
        plate_status_call = {
            'api_url': util.construct_url('lims/plate_status', match={'project_id': id_list[0], 'project_status': 'all'})
        }
        library_info_call = {
            'api_url': util.construct_url('lims/library_info', match={'project_id': id_list[0]})
        }
        sample_qc_info_call = {
            'api_url': util.construct_url('lims/sample_qc_info', match={'project_id': id_list[0]})
        }
        genotyping_info_call = {
            'api_url': util.construct_url('lims/genotyping_info', match={'project_id': id_list[0]})
        }

    procs = []
    bioinformatics_urls = []
    for i in id_list:
        docs = rest_api().get_documents(
            'analysis_driver_procs',
            where={'dataset_type': 'project', 'dataset_name': i},
            embedded={'stages': 1},
            sort='-_created'
        )
        procs.extend(docs)

        bioinformatics_urls += [
            util.construct_url('samples', where={'project_id': i}, max_results=10000),
            util.construct_url('lims/sample_status', match={'project_id': i, 'project_status': 'all'}),
            util.construct_url('lims/sample_info', match={'project_id': i, 'project_status': 'all'})
        ]

    return render_template(
        'project_report.html',
        'Project report for ' + project_ids,
        include_review_modal=True,
        tables=[
            util.datatable_cfg(
                'Project Status for ' + project_ids,
                'project_status',
                minimal=True,
                **project_status_call
            ),
            util.datatable_cfg(
                'Plate Status for ' + project_ids,
                'plate_status',
                minimal=True,
                default_sort_col='plate_id',
                collapse=True,
                **plate_status_call
            ),
            util.datatable_cfg(
                'Sample QC for ' + project_ids,
                'sample_qc',
                minimal=True,
                default_sort_col='date_completed',
                child_datatable=util.datatable_cfg(
                    '',  # No title provided
                    'sample_qc_child',
                    data_source='samples',  # Where to find the data of the child datatable
                    name_source='id',  # Where to find the name of the child datatable
                    minimal=True
                ),
                collapse=True,
                **sample_qc_info_call
            ),
            util.datatable_cfg(
                'Libraries preparations for ' + project_ids,
                'libraries',
                minimal=True,
                default_sort_col='date_completed',
                child_datatable=util.datatable_cfg(
                    '',  # No title provided
                    'libraries_child',
                    data_source='samples',  # Where to find the data of the child datatable
                    name_source='id',  # Where to find the name of the child datatable
                    minimal=True
                ),
                collapse=True,
                **library_info_call
            ),
            util.datatable_cfg(
                'Genotyping for ' + project_ids,
                'genotyping',
                minimal=True,
                default_sort_col='date_completed',
                child_datatable=util.datatable_cfg(
                    '',  # No title provided
                    'genotyping_child',
                    data_source='samples',  # Where to find the data of the child datatable
                    name_source='id',  # Where to find the name of the child datatable
                    minimal=True
                ),
                collapse=True,
                **genotyping_info_call
            ),
            util.datatable_cfg(
                'Bioinformatics report for ' + project_ids,
                'samples',
                ajax_call={
                    'func_name': 'dt_merge_multi_sources',
                    'api_urls': bioinformatics_urls,
                    'merge_on': 'sample_id'
                },
                fixed_header=True,
                review={'entity_field': 'sample_id', 'button_name': 'samplereview'},
                create_row='color_data_source'
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
        include_review_modal=True,
        tables=[
            util.datatable_cfg(
                'Sample QC for ' + sample_id,
                'sample_qc_child_flatten',
                minimal=True,
                default_sort_col='sample_id',
                api_url=util.construct_url('lims/sample_qc_info', match={'sample_id': sample_id}, flatten=True),
                collapse=True
            ),
            util.datatable_cfg(
                'Libraries preparations for ' + sample_id,
                'libraries_child_flatten',
                minimal=True,
                default_sort_col='sample_id',
                api_url=util.construct_url('lims/library_info', match={'sample_id': sample_id}, flatten=True),
                collapse=True
            ),
            util.datatable_cfg(
                'Genotyping for ' + sample_id,
                'genotyping_child_flatten',
                minimal=True,
                default_sort_col='sample_id',
                api_url=util.construct_url('lims/genotyping_info', match={'sample_id': sample_id}, flatten=True),
                collapse=True
            ),
            util.datatable_cfg(
                'Bioinformatics report for ' + sample_id,
                'samples',
                ajax_call={
                    'func_name': 'dt_merge_multi_sources',
                    'merge_on': 'sample_id',
                    'api_urls': [
                        util.construct_url('samples', where={'sample_id': sample_id}),
                        util.construct_url('lims/sample_status', match={'sample_id': sample_id, 'project_status': 'all'}),
                        util.construct_url('lims/sample_info', match={'sample_id': sample_id, 'project_status': 'all'})
                    ]
                },
                minimal=True,
                review={'entity_field': 'sample_id', 'button_name': 'samplereview'},
                create_row='color_data_source'
            ),
            util.datatable_cfg(
                'Run elements generated for ' + sample_id,
                'sample_run_elements',
                api_url=util.construct_url('run_elements', where={'sample_id': sample_id}, max_results=1000),
                minimal=True,
                create_row='color_filter'
            )
        ],
        sample_id=sample_id,
        sample_statuses=rest_api().get_document(
            'lims/status/sample_status',
            detailed=True,
            match={'sample_id': sample_id, 'project_status': 'all'}
        ),
        lims_url=cfg['lims_url'],
        procs=rest_api().get_documents(
            'analysis_driver_procs',
            where={'dataset_type': 'sample', 'dataset_name': sample_id},
            embedded={'stages': 1},
            sort='-_created'
        )
    )


@app.route('/<step_type>/<view_type>')
@flask_login.login_required
def step_view(step_type, view_type):
    if step_type == 'libraries':
        endpoint = 'library_info'
        columns = 'libraries'
        child_columns = 'libraries_child'
    elif step_type == 'genotypes':
        endpoint = 'genotyping_info'
        columns = 'genotyping'
        child_columns = 'genotyping_child'
    else:
        fl.abort(404)

    time_ago = None
    if view_type == 'recent':
        time_ago = util.now() - datetime.timedelta(days=30)
    elif view_type == 'last_12_months':
        time_ago = util.now() - datetime.timedelta(days=365)
    elif view_type == 'current_year':
        y = util.now().year
        time_ago = datetime.datetime(year=y, month=1, day=1)
        view_type = str(y)
    elif view_type == 'all':
        pass
    else:
        fl.abort(404)
        return None

    query_params = {}
    if time_ago:
        query_params['time_from'] = time_ago.strftime(settings.DATE_FORMAT)

    title = util.capitalise(view_type).replace('_', ' ') + ' ' + util.capitalise(step_type)
    return render_template(
        'untabbed_datatables.html',
        title,
        table=util.datatable_cfg(
            title,
            columns,
            util.construct_url('lims/' + endpoint, **query_params),
            default_sort_col='-date_completed',
            child_datatable=util.datatable_cfg(
                '',  # No title provided
                child_columns,
                data_source='samples', # Where to find the data of the child datatable
                name_source='id',  # Where to find the name of the child datatable
                minimal=True
            )
        )
    )


@app.route('/library/<library>')
@flask_login.login_required
def plot_library(library):
    return render_template(
        'plate_view.html',
        'Library ' + library,
        table=util.datatable_cfg(
            'Library ' + library,
            ['simple_plot_child', 'library_plot_metrics'],
            ajax_call={
                'func_name': 'dt_merge_lims_container_and_qc_data',
                'lims_url': util.construct_url('lims/library_info', match={'container_id': library}, flatten=True),
                'qc_url': util.construct_url('samples'),
            },
            initComplete='load_data_to_chart',
            page_length=10
        ),
        container_id=library,
        plate_view_metrics=resolve_cols('library_plot_metrics')
    )


@app.route('/genotype/<genotype>')
@flask_login.login_required
def plot_genotyping(genotype):
    return render_template(
        'plate_view.html',
        'Genotyping: ' + genotype,
        table=util.datatable_cfg(
            'Genotyping ' + genotype,
            ['simple_plot_child', 'genotype_plot_metrics'],
            ajax_call={
                'func_name': 'dt_merge_lims_container_and_qc_data',
                'lims_url': util.construct_url('lims/genotyping_info', match={'container_id': genotype}, flatten=True),
                'qc_url': util.construct_url('samples'),
            },
            initComplete='load_data_to_chart',
            page_length=10
        ),
        container_id=genotype,
        plate_view_metrics=resolve_cols('genotype_plot_metrics'),
        plate_type='384'
    )


@app.route('/project_status/', defaults={'prj_status': 'open'})
@app.route('/project_status/<prj_status>')
@flask_login.login_required
def project_status_reports(prj_status):
    status_order = []
    for s in project_status_cfg.status_order:
        status_order.append(
            {
                'name': s,
                'completed': [step for step, st in project_status_cfg.step_completed_to_status.items() if st == s],
                'queued': [step for step, st in project_status_cfg.step_queued_to_status.items() if st == s]
            }
        )

    # Last week project status page is a special case and needs to be rendered slightly differently.
    if prj_status == 'lastweek':
        seven_days_ago = datetime.datetime.now() - datetime.timedelta(days=7)
        page_title = 'Project status last week'
        page_header = 'Status of Projects Last Week'
        api_url = util.construct_url('lims/project_status',
                                     match={'process_limit_date': seven_days_ago.strftime(settings.DATE_FORMAT)})
    else:
        page_title = prj_status.capitalize() + ' Project Status'
        page_header = 'Status of ' + prj_status.capitalize() + ' Projects'
        api_url = util.construct_url('lims/project_status', match={'project_status': prj_status})

    return render_template(
        'project_status.html',
        page_title,
        status_order=status_order,
        table=util.datatable_cfg(
            page_header,
            'project_status',
            api_url=api_url,
            state_save=True,
            fixed_header=True,
            table_foot='sum_row_per_column'
        )
    )


@app.route('/species')
@flask_login.login_required
def all_species():
    return render_template(
        'untabbed_datatables.html',
        'Species',
        tables=[
            util.datatable_cfg(
                'Available species',
                'species',
                util.construct_url('species', max_results=1000)
            ),
            util.datatable_cfg(
                'Installed genomes',
                'genomes',
                util.construct_url('genomes', max_results=10000)
            )
        ]
    )


@app.route('/species/<species>')
@flask_login.login_required
def species_page(species):
    return render_template(
        'untabbed_datatables.html',
        species,
        tables=[
            util.datatable_cfg(
                'Summary',
                'species',
                util.construct_url('species', where={'name': species}),
                minimal=True
            ),
            util.datatable_cfg(
                'Supported genomes',
                'genomes',
                util.construct_url('genomes', where={'species': species}, max_results=1000),
                minimal=True
            ),
            util.datatable_cfg(
                'Yield requirements',
                'yields',
                ajax_call={
                    'func_name': 'required_yields',
                    'api_url': util.construct_url('species', where={'name': species})
                },
                default_sort_col='yield_x_coverage',
                minimal=True
            )
        ]
    )


@app.route('/charts/seq/<view_type>')
@flask_login.login_required
def sequencing_charts(view_type):
    if view_type == 'last_month':
        time_ago = util.now() - datetime.timedelta(days=30)
    elif view_type == 'last_3_months':
        time_ago = util.now() - datetime.timedelta(days=92)
    elif view_type == 'last_12_months':
        time_ago = util.now() - datetime.timedelta(days=365)
    else:
        fl.abort(404)
        return None
    time_str = time_ago.strftime(settings.DATE_FORMAT)
    return render_template(
        'charts.html',
        'Sequencing metrics charts',
        time_str=time_str,
        merge_on='run_id',
        merge_properties=['run'],
        metric_options=resolve_cols('seq_plot_metrics'),
        color_options=resolve_cols('seq_plot_colors')
    )


@app.route('/charts/tat')
@flask_login.login_required
def tat_charts():
    return render_template(
        'tat_charts.html',
        'Turn around time charts',
    )


@app.route('/charts/bioinformatics')
@flask_login.login_required
def bioinformatics_activity():
    return render_template(
        'bioinformatics_activity.html',
        'Bioinformatics pipeline activity'
    )
