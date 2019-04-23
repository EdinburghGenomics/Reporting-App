from egcg_core import constants
from config import schema
from rest_api import settings
from tests import Helper


class TestSchema(Helper):
    def setUp(self):
        self.constant_values = [v for k, v in constants.__dict__.items() if k.startswith('ELEMENT')]

    def test_schema_name_in_constant(self):
        list_values_in_constants = set()
        list_values_not_in_constants = set()

        # function that recursively resolve all field names present in the schema
        def resolve_dict_value_in_constant(schema_provided, islist=False):
            for field in schema_provided:
                if not islist:
                    if field in self.constant_values:
                        list_values_in_constants.add(field)
                    else:
                        list_values_not_in_constants.add(field)

                if 'schema' in schema_provided[field]:
                    resolve_dict_value_in_constant(
                        schema_provided[field]['schema'],
                        islist=schema_provided[field]['type'] == 'list'
                    )

        for endpoint in settings.DOMAIN:
            resolve_dict_value_in_constant(schema[endpoint])

        expected_not_in_constant = [
            'action_id', 'action_info', 'action_type', 'analyses_supported', 'analysis_driver_proc',
            'approximate_genome_size', 'assembly_name', 'best_matching_samples', 'chromosome_count', 'comments',
            'data_deleted', 'data_files', 'data_source', 'dataset_name', 'dataset_type', 'date_added', 'date_finished',
            'date_started', 'default_version', 'end_date', 'exit_status', 'fasta', 'files_delivered',
            'files_downloaded', 'gc_bias', 'gender_genotype', 'genome_used', 'genomes', 'goldenpath', 'mean_deviation',
            'name', 'pid', 'pipeline_used', 'project_whitelist', 'sample_pipeline', 'slope', 'species', 'stage_id',
            'stage_name', 'stages', 'start_date', 'started_by', 'taxid', 'tools_used', 'toolset_type',
            'toolset_version', 'useable_reviewer', 'variation', '0-1', '1-2', '2-5', '5-10', '10-20', '20-30', '30-40',
            '40-50', '50-100', '100+', 'pc_unique_mapped', 'pc_genome_with_coverage', 'var_calling', 'pc_duplicates',
            'pc_mapped', 'unique_mapped_reads', 'mapping', 'rapid_analysis', 'mean_coverage', 'yield', 'yield_r1',
            'yield_r2', 'pc_q30'
        ]
        assert sorted(list_values_not_in_constants) == sorted(expected_not_in_constant)

        in_constants_not_in_schema = set(self.constant_values).difference(list_values_in_constants)
        assert sorted(in_constants_not_in_schema) == ['Nb secondary alignments', 'project', 'samtools_median_coverage']
