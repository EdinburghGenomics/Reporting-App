from unittest.mock import patch, Mock, PropertyMock
from rest_api.actions import automatic_review as ar
from rest_api.actions.automatic_review import AutomaticSampleReviewer
from rest_api.aggregation.database_side import queries
from tests.test_rest_api import TestBase

ppath = 'rest_api.actions.automatic_review.'

passing_lane = {
    'run_id': 'a_run', 'pc_q30': 83.01, 'lane_number': 1, 'pc_pass_filter': 75.27, 'yield_in_gb': 140.29, 'lane_pc_optical_dups': 9
}

failing_lanes = [
    {'run_id': 'a_run', 'pc_q30': 77.14, 'pc_pass_filter': 39.87, 'yield_in_gb': 74.30, 'lane_number': 2, 'lane_pc_optical_dups': 26},
    {'run_id': 'a_run', 'pc_q30': 74.97, 'pc_pass_filter': 40.17, 'yield_in_gb': 74.86, 'lane_number': 3, 'lane_pc_optical_dups': 10}
]

run_elements = [{'barcode': 'b1'}, {'barcode': 'b2'}]

failing_sample = {
    'sample_id': 'sample1',
    'expected_yield_q30': 95,
    'pc_mapped_reads': 97.18,
    'provided_gender': 'female',
    'clean_yield_in_gb': 114.31,
    'called_gender': 'male',
    'genotype_validation': {'mismatching_snps': 3, 'no_call_chip': 1, 'no_call_seq': 0, 'matching_snps': 28},
    'pc_duplicate_reads': 16.20,
    'coverage': {'mean': 30.156},
    'clean_yield_q30': 89.33
}

passing_sample = {
    'sample_id': 'sample1',
    'expected_yield_q30': 95,
    'species_name': 'Homo sapiens',
    'genotype_validation': {'mismatching_snps': 1, 'no_call_seq': 0, 'no_call_chip': 3, 'matching_snps': 28},
    'provided_gender': 'female',
    'clean_yield_in_gb': 120.17,
    'clean_yield_q30': 95.82,
    'called_gender': 'female',
    'coverage': {'mean': 30.34},
    'pc_mapped_reads': 95.62,
    'pc_duplicate_reads': 20
}

sample_no_genotype = {
    'sample_id': 'sample1',
    'species_name': 'Homo sapiens',
    'expected_yield_q30': 95,
    # 'genotype_validation': None,
    'provided_gender': 'female',
    'clean_yield_in_gb': 120.17,
    'clean_yield_q30': 95.82,
    'called_gender': 'female',
    'median_coverage': 30.34,
    'pc_mapped_reads': 95.62,
    'pc_duplicate_reads': 20
}

non_human_sample = {
    'sample_id': 'sample1',
    'species_name': 'Bos torus',
    'clean_yield_in_gb': 120.17,
    'clean_yield_q30': 95.82,
    'median_coverage': 30.34,
    'pc_mapped_reads': 95.62,
    'pc_duplicate_reads': 20
}


class TestLaneReviewer(TestBase):
    def setUp(self):
        self.passing_reviewer = ar.AutomaticLaneReviewer(passing_lane)
        self.failing_reviewer_1 = ar.AutomaticLaneReviewer(failing_lanes[0])
        self.failing_reviewer_2 = ar.AutomaticLaneReviewer(failing_lanes[1])

    def test_failing_metrics(self):
        assert self.passing_reviewer.get_failing_metrics() == []
        assert self.failing_reviewer_1.get_failing_metrics() == ['lane_pc_optical_dups', 'yield_in_gb']
        assert self.failing_reviewer_2.get_failing_metrics() == ['pc_q30', 'yield_in_gb']

    @patch(ppath + 'AutomaticLaneReviewer.get_failing_metrics', return_value=[])
    def test_summary_pass(self, mocked_get_failing_metrics):
        assert self.passing_reviewer._summary['reviewed'] == 'pass'
        assert 'review_date' in self.passing_reviewer._summary

    @patch(ppath + 'AutomaticLaneReviewer.get_failing_metrics', return_value=['some', 'failing', 'metrics'])
    def test_summary_fail(self, mocked_get_failing_metrics):
        assert self.passing_reviewer._summary['reviewed'] == 'fail'
        assert 'review_date' in self.passing_reviewer._summary
        assert self.passing_reviewer._summary['review_comments'] == 'failed due to some, failing, metrics'

    @patch(ppath + 'get', return_value=({'data': run_elements}, ))
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
        with patch(ppath + '_aggregate', return_value=(passing_sample,)) as patch_aggregate, self.patch_lims_samples:
            _ = self.reviewer.reviewable_data
            patch_aggregate.assert_called_once_with(
                'samples', queries.sample, request_args={'match': '{"sample_id": "sample1"}'}
            )

    def test_failing_metrics(self):
        with patch(ppath + '_aggregate', return_value=(passing_sample,)), self.patch_lims_samples:
            assert self.reviewer.get_failing_metrics() == []

        with patch(ppath + '_aggregate', return_value=(failing_sample,)), self.patch_lims_samples:
            assert self.reviewer1.get_failing_metrics() == ['clean_yield_in_gb', 'clean_yield_q30']

    def test_cfg(self):
        with patch(ppath + '_aggregate', return_value=(sample_no_genotype,)), self.patch_lims_samples:
            assert 'genotype_validation.no_call_seq' not in self.reviewer.cfg
            assert 'genotype_validation.mismatching_snps' not in self.reviewer.cfg
            assert self.reviewer.cfg['clean_yield_in_gb']['value'] == 120
            assert self.reviewer.cfg['coverage.mean']['value'] == 30

        with patch(ppath + '_aggregate', return_value=(passing_sample,)), self.patch_lims_samples:
            assert 'genotype_validation.no_call_seq' in self.reviewer1.cfg
            assert 'genotype_validation.mismatching_snps' in self.reviewer1.cfg
            assert self.reviewer1.cfg['clean_yield_in_gb']['value'] == 120
            assert self.reviewer1.cfg['coverage.mean']['value'] == 30

    def test_summary(self):
        with patch(ppath + '_aggregate', return_value=(failing_sample,)), self.patch_lims_samples:
            assert self.reviewer._summary == {
                'reviewed': 'fail',
                'review_comments': 'failed due to Yield, Yield Q30',
                'review_date': self.reviewer.current_time
            }

    @patch(ppath + 'patch_internal')
    def test_push_review(self, mocked_patch):
        with patch(ppath + '_aggregate', return_value=(passing_sample,)), self.patch_lims_samples:
            self.reviewer.push_review()
            mocked_patch.assert_called_with(
                'samples',
                payload={'reviewed': 'pass', 'review_comments': 'pass', 'review_date': self.reviewer.current_time},
                sample_id='sample1'
            )
