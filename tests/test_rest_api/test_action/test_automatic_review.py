from unittest.mock import patch, Mock, PropertyMock

import pytest
import werkzeug

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
            'pc_pass_filter': 39.87,
            'yield_in_gb': 74.30,
            'pc_opt_duplicate_reads': 30.1,
            'pc_adaptor': 2.3
        }
    },
    {
        'run_id': 'a_run',
        'lane_number': 3,
        'aggregated': {
            'pc_q30': 74.97,
            'pc_pass_filter': 40.17,
            'yield_in_gb': 74.86,
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
            "yield_in_gb": 1096.2,
            "pc_opt_duplicate_reads": 22.59,
            'pc_adaptor': 1.3
        }
    },
    {
        'run_id': 'run2',
        'aggregated': {
            'pc_q30': 81.5,
            "yield_in_gb": 920.12,
            "pc_opt_duplicate_reads": 30.59,
            'pc_adaptor': 0.8
        }
    }
]

run_elements = [{'barcode': 'b1', 'lane': 1}, {'barcode': 'b2', 'lane': 1}]

failing_sample = {
    'sample_id': 'sample1',
    'expected_yield_q30': 95,
    'provided_gender': 'female',
    'called_gender': 'male',
    'genotype_validation': {'mismatching_snps': 3, 'no_call_chip': 1, 'no_call_seq': 0, 'matching_snps': 28},
    'coverage': {'mean': 30.156},
    'aggregated': {
        'pc_mapped_reads': 97.18,
        'clean_yield_in_gb': 114.31,
        'pc_duplicate_reads': 16.20,
        'clean_yield_q30': 89.33
    }
}

passing_sample = {
    'sample_id': 'sample1',
    'expected_yield_q30': 95,
    'species_name': 'Homo sapiens',
    'genotype_validation': {'mismatching_snps': 1, 'no_call_seq': 0, 'no_call_chip': 3, 'matching_snps': 28},
    'provided_gender': 'female',
    'called_gender': 'female',
    'coverage': {'mean': 30.34},
    'aggregated': {
        'clean_yield_in_gb': 120.17,
        'clean_yield_q30': 95.82,
        'pc_mapped_reads': 95.62,
        'pc_duplicate_reads': 20
    }
}

sample_no_genotype = {
    'sample_id': 'sample1',
    'species_name': 'Homo sapiens',
    'expected_yield_q30': 95,
    'provided_gender': 'female',
    'called_gender': 'female',
    'median_coverage': 30.34,
    'aggregated': {
        'pc_mapped_reads': 95.62,
        'pc_duplicate_reads': 20,
        'clean_yield_in_gb': 120.17,
        'clean_yield_q30': 95.82
    }
}

non_human_sample = {
    'sample_id': 'sample1',
    'species_name': 'Bos torus',
    'median_coverage': 30.34,
    'aggregated': {
        'clean_yield_in_gb': 120.17,
        'clean_yield_q30': 95.82,
        'pc_mapped_reads': 95.62,
        'pc_duplicate_reads': 20
    }
}


class TestRunReviewer(TestBase):

    def setUp(self):
        self.init_request = Mock(form={'run_id': 'run1'})
        with patch.object(AutomaticLaneReviewer, 'eve_get', return_value=[passing_lane]):
            self.reviewer1 = ar.AutomaticRunReviewer(self.init_request)

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
                    payload={'review_date': self.reviewer1.current_time, 'review_comments': 'failed due to Run PC Q30', 'reviewed': 'fail'}
                )
                mocked_patch.assert_called_with(
                    'run_elements', lane=1, run_id='run1', barcode='b2',
                    payload={'review_date': self.reviewer1.current_time, 'review_comments': 'failed due to Run PC Q30', 'reviewed': 'fail'}
                )

    def test_unknown_run(self):
        with patch.object(AutomaticLaneReviewer, 'eve_get', return_value=[]):
            with pytest.raises(werkzeug.exceptions.NotFound):
                _ = AutomaticRunReviewer(Mock(form={'run_id': 'unknown_run'}))


class TestLaneReviewer(TestBase):
    def setUp(self):
        self.passing_reviewer = ar.AutomaticLaneReviewer(passing_lane)
        self.failing_reviewer_1 = ar.AutomaticLaneReviewer(failing_lanes[0])
        self.failing_reviewer_2 = ar.AutomaticLaneReviewer(failing_lanes[1])

    def test_failing_metrics(self):
        assert self.passing_reviewer.failing_metrics == []
        assert self.failing_reviewer_1.failing_metrics == ['aggregated.pc_opt_duplicate_reads', 'aggregated.yield_in_gb']
        assert self.failing_reviewer_2.failing_metrics == ['aggregated.pc_q30', 'aggregated.yield_in_gb']

    def test_summary_pass(self):
        assert self.passing_reviewer._summary['reviewed'] == 'pass'
        assert 'review_date' in self.passing_reviewer._summary

    def test_summary_fail(self):
        assert self.failing_reviewer_1._summary['reviewed'] == 'fail'
        assert 'review_date' in self.failing_reviewer_1._summary
        assert self.failing_reviewer_1._summary['review_comments'] == 'failed due to Optical duplicate rate, Yield'

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
            assert self.reviewer1.failing_metrics == ['aggregated.clean_yield_in_gb', 'aggregated.clean_yield_q30']

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
                'review_comments': 'failed due to Yield, Yield Q30',
                'review_date': self.reviewer.current_time
            }

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
                reviewer.reviewable_data
