from unittest.mock import patch, Mock, PropertyMock

import pytest
import werkzeug
from rest_api import app
from rest_api.actions import automatic_review as ar, AutomaticRunReviewer
from rest_api.actions.automatic_review import AutomaticSampleReviewer, AutomaticLaneReviewer
from tests.test_rest_api import TestBase

ppath = 'rest_api.actions.automatic_review.'

passing_lane = {
    'run_id': 'a_run',
    'lane_number': 1,
    'aggregated': {
        'pc_pass_filter': 75.27,
        'yield_in_gb': 140.29,
        'pc_q30': 83.01,
        'pc_q30_r1': 89.21,
        'pc_q30_r2': 78.14,
        'pc_duplicate_reads': 22.1,
        'pc_opt_duplicate_reads': 21.1,
        'pc_adaptor': 0.5
    }
}

failing_lanes = [
    {
        'run_id': 'a_run',
        'lane_number': 2,
        'aggregated': {
            'pc_q30': 77.14,
            'pc_q30_r1': 80.12,
            'pc_q30_r2': 74.9,
            'pc_pass_filter': 39.87,
            'yield_in_gb': 74.30,
            'pc_duplicate_reads': 31.5,
            'pc_opt_duplicate_reads': 30.1,
            'pc_adaptor': 2.3
        }
    },
    {
        'run_id': 'a_run',
        'lane_number': 3,
        'aggregated': {
            'pc_q30': 74.97,
            'pc_q30_r1': 79.12,
            'pc_q30_r2': 71.2,
            'pc_pass_filter': 40.17,
            'yield_in_gb': 74.86,
            'pc_duplicate_reads': 22.9,
            'pc_opt_duplicate_reads': 21.1,
            'pc_adaptor': 0.3
        }
    }
]

failing_runs = [
    {
        'run_id': 'run1',
        'aggregated': {
            'pc_q30': 73.4,
            'pc_q30_r1': 76.1,
            'pc_q30_r2': 70.6,
            "yield_in_gb": 1096.2,
            "pc_duplicate_reads": 22.59,
            'pc_opt_duplicate_reads': 21.1,
            'pc_adaptor': 1.3
        }
    },
    {
        'run_id': 'run2',
        'aggregated': {
            'pc_q30': 81.5,
            "yield_in_gb": 920.12,
            "pc_duplicate_reads": 30.59,
            'pc_opt_duplicate_reads': 21.1,
            'pc_adaptor': 0.8
        }
    }
]

run_elements = [{'barcode': 'b1', 'lane': 1}, {'barcode': 'b2', 'lane': 1}]

failing_sample = {
    'sample_id': 'sample1',
    'required_yield_q30': 95000000000,
    'required_coverage': 30,
    'required_yield': 120000000000,
    'genotype_validation': {'mismatching_snps': 3, 'no_call_chip': 1, 'no_call_seq': 0, 'matching_snps': 28},
    'coverage': {'mean': 30.156},
    'aggregated': {
        'pc_mapped_reads': 97.18,
        'clean_yield_in_gb': 114.31,
        'pc_duplicate_reads': 16.20,
        'clean_yield_q30_in_gb': 89.33
    }
}


passing_sample = {
    'sample_id': 'sample1',
    'required_yield_q30': 95000000000,
    'required_coverage': 30,
    'required_yield': 120000000000,
    'species_name': 'Homo sapiens',
    'genotype_validation': {'mismatching_snps': 1, 'no_call_seq': 0, 'no_call_chip': 3, 'matching_snps': 28},
    'coverage': {'mean': 30.34},
    'aggregated': {
        'clean_yield_in_gb': 120.17,
        'clean_yield_q30_in_gb': 95.82,
        'pc_mapped_reads': 95.62,
        'pc_duplicate_reads': 20
    }
}

sample_failing_genotype = {
    'sample_id': 'sample1',
    'required_yield_q30': 95000000000,
    'required_coverage': 30,
    'required_yield': 120000000000,
    'species_name': 'Homo sapiens',
    'genotype_validation': {'mismatching_snps': 12, 'no_call_seq': 0, 'no_call_chip': 3, 'matching_snps': 16},
    'coverage': {'mean': 30.34},
    'aggregated': {
        'clean_yield_in_gb': 120.17,
        'clean_yield_q30_in_gb': 95.82,
        'pc_mapped_reads': 95.62,
        'pc_duplicate_reads': 20
    }
}
sample_no_genotype = {
    'sample_id': 'sample1',
    'species_name': 'Homo sapiens',
    'required_yield_q30': 95000000000,
    'required_coverage': 30,
    'required_yield': 120000000000,
    'coverage': {'mean': 30.34},
    'aggregated': {
        'pc_mapped_reads': 95.62,
        'pc_duplicate_reads': 20,
        'clean_yield_in_gb': 120.17,
        'clean_yield_q30_in_gb': 95.82
    }
}

non_human_sample = {
    'sample_id': 'sample1',
    'species_name': 'Bos torus',
    'median_coverage': 30.34,
    'aggregated': {
        'clean_yield_in_gb': 120.17,
        'clean_yield_q30_in_gb': 95.82,
        'pc_mapped_reads': 95.62,
        'pc_duplicate_reads': 20
    }
}


class TestRunReviewer(TestBase):
    def setUp(self):
        self.init_request = Mock(form={'run_id': 'run1'})
        with patch.object(AutomaticLaneReviewer, 'eve_get', return_value=[passing_lane]):
            self.reviewer1 = ar.AutomaticRunReviewer(self.init_request)

    def test_eve_get(self):
        page1 = {'data': ['test1'], '_links': {'next': {'href': 'endpoint?page=2'}}}
        page2 = {'data': ['test2'], '_links': {'next': {'href': 'endpoint?page=3'}}}
        page3 = {'data': ['test3'], '_links': {}}

        with patch('rest_api.actions.automatic_review.get', side_effect=[(page1,), (page2,), (page3,)]) as mock_get:
            with app.test_request_context():
                assert self.reviewer1.eve_get('endpoint', param1='this') == ['test1', 'test2', 'test3']
                assert mock_get.call_count == 3
                mock_get.assert_called_with('endpoint', param1='this')

    def test_reviewable_data(self):
        with patch.object(AutomaticLaneReviewer, 'eve_get', return_value=(failing_runs[0],)) as patch_get:
            assert self.reviewer1.reviewable_data == failing_runs[0]
            patch_get.assert_called_once_with('runs', run_id='run1')

    def test_perform_action(self):
        with patch.object(AutomaticRunReviewer, 'reviewable_data', new_callable=PropertyMock(return_value=failing_runs[0])), \
             patch.object(AutomaticRunReviewer, 'run_elements', new_callable=PropertyMock(return_value=run_elements)), \
             patch(ppath + 'patch_internal') as mocked_patch:
                self.reviewer1._perform_action()
                mocked_patch.assert_any_call(
                    'run_elements', lane=1, run_id='run1', barcode='b1',
                    payload={
                        'review_date': self.reviewer1.current_time,
                        'review_comments': 'Failed due to Run PC Q30 < 75',
                        'reviewed': 'fail'
                    }
                )
                mocked_patch.assert_called_with(
                    'run_elements', lane=1, run_id='run1', barcode='b2',
                    payload={
                        'review_date': self.reviewer1.current_time,
                        'review_comments': 'Failed due to Run PC Q30 < 75',
                        'reviewed': 'fail'}
                )

    def test_unknown_run(self):
        with patch.object(AutomaticLaneReviewer, 'eve_get', return_value=[]):
            with pytest.raises(werkzeug.exceptions.NotFound):
                _ = AutomaticRunReviewer(Mock(form={'run_id': 'unknown_run'}))

    def test_resolve_formula(self):
        data = {'this': {
            'value': 3,
            'other_value': 5
        }}
        formula = 'this.value * (10 - this.other_value) + 1'
        assert self.reviewer1.resolve_formula(data, formula) == 16

        formula = 'this.non_existing_value * (10 - this.other_value) + 1'
        assert self.reviewer1.resolve_formula(data, formula) is None


class TestLaneReviewer(TestBase):
    def setUp(self):
        self.passing_reviewer = ar.AutomaticLaneReviewer(passing_lane)
        self.failing_reviewer_1 = ar.AutomaticLaneReviewer(failing_lanes[0])
        self.failing_reviewer_2 = ar.AutomaticLaneReviewer(failing_lanes[1])

    def test_failing_metrics(self):
        assert self.passing_reviewer.failing_metrics == []
        assert self.failing_reviewer_1.failing_metrics == [
            'aggregated.pc_opt_duplicate_reads', 'aggregated.yield_in_gb', 'compound_yield_adapter_duplicates'
        ]
        assert self.failing_reviewer_2.failing_metrics == [
            'aggregated.pc_q30', 'aggregated.yield_in_gb', 'compound_yield_adapter_duplicates'
        ]

    def test_summary_pass(self):
        assert self.passing_reviewer._summary['reviewed'] == 'pass'
        assert 'review_date' in self.passing_reviewer._summary

    def test_summary_fail(self):
        assert self.failing_reviewer_1._summary['reviewed'] == 'fail'
        assert 'review_date' in self.failing_reviewer_1._summary
        assert self.failing_reviewer_1._summary['review_comments'] == \
               'Failed due to Optical duplicate rate > 30, Yield < 120, Yield with no adapters and no duplicates < 96'

    def test_get_failure_comment(self):
        assert self.failing_reviewer_1.failure_comment == \
               'Failed due to Optical duplicate rate > 30, Yield < 120, Yield with no adapters and no duplicates < 96'

    @patch.object(AutomaticLaneReviewer, 'eve_get', return_value=run_elements)
    @patch(ppath + 'patch_internal')
    def test_push_review(self, mocked_patch, mocked_get):
        self.passing_reviewer.push_review()
        mocked_patch.assert_any_call(
            'run_elements',
            lane=1,
            run_id='a_run',
            barcode='b1',
            payload={'review_date': self.passing_reviewer.current_time, 'review_comments': 'pass', 'reviewed': 'pass'}
        )
        mocked_patch.assert_called_with(
            'run_elements',
            lane=1,
            run_id='a_run',
            barcode='b2',
            payload={'review_date': self.passing_reviewer.current_time, 'review_comments': 'pass', 'reviewed': 'pass'}
        )


class TestSampleReviewer(TestBase):

    def setUp(self):
        self.init_request = Mock(form={'sample_id': 'sample1'})
        self.fake_sample = Mock(udf={
            'Yield for Quoted Coverage (Gb)': 95,
            'Required Yield (Gb)': 120,
            'Coverage (X)': 30
        })
        self.patch_lims_samples = patch.object(
            AutomaticSampleReviewer,
            'lims_sample',
            new_callable=PropertyMock(return_value=self.fake_sample)
        )
        self.reviewer = ar.AutomaticSampleReviewer(self.init_request)
        self.reviewer1 = ar.AutomaticSampleReviewer(self.init_request)

    def test_reviewable_data(self):
        with patch.object(AutomaticSampleReviewer, 'eve_get', return_value=(passing_sample,)) as patch_get, \
             self.patch_lims_samples:
            _ = self.reviewer.reviewable_data
            patch_get.assert_called_once_with('samples', sample_id="sample1")

    def test_failing_metrics(self):
        with patch.object(AutomaticSampleReviewer, 'eve_get', return_value=(passing_sample,)), self.patch_lims_samples:
            assert self.reviewer.failing_metrics == []

        with patch.object(AutomaticSampleReviewer, 'eve_get', return_value=(failing_sample,)), self.patch_lims_samples:
            assert self.reviewer1.failing_metrics == ['aggregated.clean_yield_in_gb']

    def test_cfg(self):
        with patch.object(AutomaticSampleReviewer, 'eve_get', return_value=(sample_no_genotype,)), self.patch_lims_samples:
            assert 'genotype_validation.no_call_seq' not in self.reviewer.cfg
            assert 'genotype_validation.mismatching_snps' not in self.reviewer.cfg
            assert self.reviewer.cfg['aggregated.clean_yield_in_gb']['value'] == 120
            assert self.reviewer.cfg['coverage.mean']['value'] == 30

        with patch.object(AutomaticSampleReviewer, 'eve_get', return_value=(passing_sample,)), self.patch_lims_samples:
            assert 'genotype_validation.no_call_seq' in self.reviewer1.cfg
            assert 'genotype_validation.mismatching_snps' in self.reviewer1.cfg
            assert self.reviewer1.cfg['aggregated.clean_yield_in_gb']['value'] == 120
            assert self.reviewer1.cfg['coverage.mean']['value'] == 30

    def test_summary(self):
        with patch.object(AutomaticSampleReviewer, 'eve_get', return_value=(failing_sample,)), self.patch_lims_samples:
            assert self.reviewer._summary == {
                'reviewed': 'fail',
                'review_comments': 'Failed due to Yield < 120',
                'review_date': self.reviewer.current_time
            }

    def test_get_failure_comment(self):
        with patch.object(AutomaticSampleReviewer, 'eve_get', return_value=(sample_failing_genotype,)), \
             self.patch_lims_samples:
            assert self.reviewer.failure_comment == 'Failed due to Genotyping error > 5'

    @patch(ppath + 'patch_internal')
    def test_push_review(self, mocked_patch):
        with patch.object(AutomaticSampleReviewer, 'eve_get', return_value=(passing_sample,)), self.patch_lims_samples:
            self.reviewer.push_review()

            mocked_patch.assert_called_with(
                'samples',
                payload={'reviewed': 'pass', 'review_comments': 'pass', 'review_date': self.reviewer.current_time},
                sample_id='sample1'
            )

    def test_unknown_sample(self):
        with patch.object(AutomaticSampleReviewer, 'eve_get', return_value=[]):
            with pytest.raises(werkzeug.exceptions.NotFound):
                reviewer = AutomaticSampleReviewer(Mock(form={'sample_id': 'unknown_sample'}))
                _ = reviewer.reviewable_data
