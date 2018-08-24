from unittest.mock import Mock, patch
from tests import Helper
from datetime import datetime
from config import reporting_app_config as cfg, col_mappings
import reporting_app


def fake_api_url(endpoint):
    return '/api/0.1/' + endpoint


fake_procs = [
    {
        'proc_id': 'a_proc',
        '_created': '12_12_2017_12:00:00',
        'end_date': '12_12_2017_14:00:00',
        'status': 'finished',
        'dataset_type': 'a_type',
        'dataset_name': 'a_dataset',
        'pipeline_used': {'name': 'a_pipeline', 'toolset_version': 0, 'toolset_type': 'a_toolset_type'},
        'stages': [
            {
                'date_started': '12_12_2017_12:00:00', 'date_finished': '12_12_2017_13:00:00',
                'stage_name': 'stage_1', 'exit_status': 0
            },
            {
                'date_started': '12_12_2017_13:00:00', 'date_finished': '12_12_2017_14:00:00',
                'stage_name': 'stage_2', 'exit_status': 0
            }
        ]
    },
    {
        'proc_id': 'another_proc',
        '_created': '11_12_2017_12:00:00',
        'end_date': '11_12_2017_14:00:00',
        'status': 'finished',
        'dataset_type': 'a_type',
        'dataset_name': 'a_dataset',
        'pipeline_used': {'name': 'a_pipeline', 'toolset_version': 0, 'toolset_type': 'a_toolset_type'},
        'stages': [
            {
                'date_started': '11_12_2017_12:00:00', 'date_finished': '11_12_2017_13:00:00',
                'stage_name': 'stage_1', 'exit_status': 0
            },
            {
                'date_started': '11_12_2017_13:00:00', 'date_finished': '11_12_2017_14:00:00',
                'stage_name': 'stage_2', 'exit_status': 0
            }
        ]
    }
]


class TestReportingApp(Helper):
    patched_current_user = patch(
        'reporting_app.flask_login.current_user',
        new=Mock(
            comm=Mock(api_url=fake_api_url),
            get_auth_token=Mock(return_value='an_auth_token'),
            username='a_user'
        )
    )
    patched_get_token = patch('reporting_app.util.get_token', return_value='a_token')

    @classmethod
    def setUpClass(cls):
        reporting_app.app.testing = True
        cls.client = reporting_app.app.test_client()
        cls.mocked_current_user = cls.patched_current_user.start()
        cls.patched_get_token.start()

    @classmethod
    def tearDownClass(cls):
        cls.patched_current_user.stop()
        cls.patched_get_token.stop()

    def test_format_order(self):
        cols = (
            {'data': 'this', 'title': 'This'},
            {'data': 'that', 'title': 'That'},
            {'data': 'other', 'title': 'Other'},
            {'data': 'another', 'title': 'Another'}
        )
        assert reporting_app.util._format_order('this', cols) == [0, 'asc']
        assert reporting_app.util._format_order('-other', cols) == [2, 'desc']

    def test_datatable_cfg(self):
        obs = reporting_app.util.datatable_cfg(
            'A Datatable',
            'demultiplexing',
            cfg['rest_api'] + '/test_endpoint',
            default_sort_col='-sample_id'
        )
        exp = {
            'title': 'A Datatable',
            'name': 'a_datatable',
            'cols': col_mappings['demultiplexing'],
            'api_url': cfg['rest_api'] + '/test_endpoint',
            'ajax_call': None,
            'default_sort_col': [2, 'desc'],
            'token': 'a_token'
        }
        assert obs == exp

    def test_tab_set_cfg(self):
        assert reporting_app.util.tab_set_cfg('A Tab Set', ['a_dt_cfg']) == {
            'title': 'A Tab Set', 'name': 'a_tab_set', 'tables': ['a_dt_cfg']
        }

    def _test_render_template(self, url):
        response = self.client.get(url)
        assert response.status_code == 200
        assert response.data

        with patch('reporting_app.render_template', return_value='some web content') as mocked_render:
            response = self.client.get(url)
            assert response.status_code == 200
            assert response.data == b'some web content'

        assert mocked_render.call_count
        return mocked_render

    def test_main_page(self):
        self._test_render_template('/')

    def test_login(self):
        self._test_render_template('/login')

    @patch('auth.check_user_auth')
    def test_login_attempt(self, mocked_check_auth):
        mocked_check_auth.return_value = True
        response = self.client.post(
            '/login',
            data={'redirect': 'a_redirect', 'username': 'a_user', 'pw': 'a_password'}
        )
        assert response.status_code == 302

        mocked_check_auth.return_value = False
        response = self.client.post(
            '/login',
            data={'redirect': 'a_redirect', 'username': 'a_user', 'pw': 'a_password'}
        )
        assert response.status_code == 200
        assert 'Bad login.' in response.data.decode('utf-8')

    def test_logout(self):
        self._test_render_template('/logout')

    def test_change_password(self):
        self._test_render_template('/change_password')

    @patch('auth.change_pw')
    def test_change_password_attempt(self, mocked_change_pw):
        mocked_change_pw.return_value = True
        response = self.client.post(
            '/change_password',
            data={'old_pw': 'an_old_pw', 'new_pw': 'a_new_pw'}
        )
        assert response.status_code == 302

        mocked_change_pw.return_value = False
        response = self.client.post(
            '/change_password',
            data={'old_pw': 'an_old_pw', 'new_pw': 'a_new_pw'}
        )
        assert response.status_code == 200
        assert 'Bad request.' in response.data.decode('utf-8')

    @patch('reporting_app.util.datatable_cfg', return_value='a_datatable_cfg')
    @patch('reporting_app.util.now', return_value=datetime(2017, 12, 12, 0, 0, 0))
    def test_runs_report(self, mocked_datetime, mocked_cfg):
        for endpoint, title in (('all', 'All'), ('recent', 'Recent'), ('current_year', '2017'), ('year_to_date', 'Year to date')):
            mocked_render = self._test_render_template('/runs/' + endpoint)
            mocked_render.assert_called_with('untabbed_datatables.html', title + ' Runs', include_review_modal=True, table='a_datatable_cfg')

        assert b'404 Not Found' in self.client.get('/runs/invalid_view').data

        mocked_cfg.assert_any_call(
            'All Runs',
            'runs',
            ajax_call={
                'func_name': 'merge_multi_sources',
                'merge_on': 'run_id',
                'api_urls': ['/api/0.1/runs?max_results=10000', '/api/0.1/lims/run_status']
            },
            create_row='color_filter',
            fixed_header=True,
            review={'entity_field': 'sample_ids', 'button_name': 'runreview'}
        )
        mocked_cfg.assert_any_call(
            'Recent Runs',
            'runs',
            ajax_call={
                'func_name': 'merge_multi_sources',
                'merge_on': 'run_id',
                'api_urls': [
                    '/api/0.1/runs?max_results=10000&where={"_created":{"$gte":"12_11_2017_00:00:00"}}',
                    '/api/0.1/lims/run_status?createddate=12_11_2017_00:00:00'
                ]
            },
            create_row='color_filter',
            fixed_header=True,
            review={'entity_field': 'sample_ids', 'button_name': 'runreview'}
        )
        mocked_cfg.assert_any_call(
            'Year to date Runs',
            'runs',
            ajax_call={
                'func_name': 'merge_multi_sources',
                'merge_on': 'run_id',
                'api_urls': [
                    '/api/0.1/runs?max_results=10000&where={"_created":{"$gte":"12_12_2016_00:00:00"}}',
                    '/api/0.1/lims/run_status?createddate=12_12_2016_00:00:00'
                ]
            },
            create_row='color_filter',
            fixed_header=True,
            review={'entity_field': 'sample_ids', 'button_name': 'runreview'}
        )
        mocked_cfg.assert_any_call(
            '2017 Runs',
            'runs',
            ajax_call={
                'func_name': 'merge_multi_sources',
                'merge_on': 'run_id',
                'api_urls': [
                    '/api/0.1/runs?max_results=10000&where={"_created":{"$gte":"01_01_2017_00:00:00"}}',
                    '/api/0.1/lims/run_status?createddate=01_01_2017_00:00:00'
                ]
            },
            create_row='color_filter',
            fixed_header=True,
            review={'entity_field': 'sample_ids', 'button_name': 'runreview'}
        )

    @patch('reporting_app.rest_api')
    def test_report_run(self, mocked_rest_api):
        mocked_rest_api.return_value.get_documents.side_effect = [
            [{'lane_number': 1}, {'lane_number': 2}],
            fake_procs,
            [{'lane_number': 1}, {'lane_number': 2}],  # _test_render_template runs the function twice
            fake_procs
        ]
        self._test_render_template('/run/a_run')

    @patch('reporting_app.rest_api', return_value=fake_procs)
    def test_project_reports(self, mocked_rest_api):
        self._test_render_template('/projects/')

    @patch('reporting_app.util.datatable_cfg', return_value='a_datatable_cfg')
    @patch('reporting_app.util.now', return_value=datetime(2017, 12, 12, 0, 0, 0))
    def test_report_samples(self, mocked_datetime, mocked_cfg):
        mocked_render = self._test_render_template('/samples/all')
        mocked_render.assert_called_with(
            'untabbed_datatables.html',
            'All samples',
            include_review_modal=True,
            table='a_datatable_cfg'
        )
        mocked_cfg.assert_called_with(
            'All samples',
            'samples',
            ajax_call={
                'func_name': 'merge_multi_sources_keep_first',
                'merge_on': 'sample_id',
                'api_urls': [
                    '/api/0.1/samples?max_results=15000',
                    '/api/0.1/lims/sample_status?match={"project_status":"all"}',
                    '/api/0.1/lims/sample_info?match={"project_status":"all"}'
                ]
            },
            review={'entity_field': 'sample_id', 'button_name': 'samplereview'},
            create_row='color_data_source'
        )

        mocked_render = self._test_render_template('/samples/toreview')
        mocked_render.assert_called_with(
            'untabbed_datatables.html',
            'Samples to review',
            include_review_modal=True,
            table='a_datatable_cfg'
        )
        mocked_cfg.assert_called_with(
            'Samples to review',
            'samples',
            ajax_call={
                'func_name': 'merge_multi_sources_keep_first',
                'merge_on': 'sample_id',
                'api_urls': [
                    '/api/0.1/samples?max_results=10000&where={"aggregated.most_recent_proc.status":"finished","useable":"not%20marked"}',
                    '/api/0.1/lims/sample_status?match={"createddate":"13_06_2017_00:00:00","project_status":"open"}',
                    '/api/0.1/lims/sample_info?match={"createddate":"13_06_2017_00:00:00","project_status":"open"}'
                ]
            },
            review={'entity_field': 'sample_id', 'button_name': 'samplereview'},
            create_row='color_data_source'
        )

    @patch('reporting_app.rest_api')
    def test_report_project(self, mocked_rest_api):
        self._test_render_template('/projects/a_project')

    @patch('reporting_app.rest_api')
    def test_report_sample(self, mocked_rest_api):
        mocked_rest_api.return_value.get_document.return_value = {
            'current_status': 'finished',
            'statuses': [
                {
                    'date': 'Dec 11 2017',
                    'name': 'a_workflow',
                    'processes': [
                        {'date': 'Dec 11 2017', 'process_id': 1337, 'type': 'complete', 'name': 'A Process'},
                        {'date': 'Dec 12 2017', 'process_id': 1338, 'type': 'complete', 'name': 'Another Process'}
                    ]
                },
                {
                    'date': 'Dec 12 2017',
                    'name': 'another_workflow',
                    'processes': [
                        {'date': 'Dec 12 2017', 'process_id': 1339, 'type': 'complete', 'name': 'Yet Another Process'}
                    ]
                }
            ]
        }
        mocked_rest_api.return_value.get_documents.return_value = fake_procs
        self._test_render_template('/sample/a_sample')

    def test_plotting_report(self):
        self._test_render_template('/charts')

    def test_project_status_report(self):
        self._test_render_template('/project_status/')
