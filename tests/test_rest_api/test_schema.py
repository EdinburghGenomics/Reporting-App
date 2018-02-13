from egcg_core import constants

from config import schema
from tests import Helper


class TestSchema(Helper):
    def setUp(self):
        self.constant_values = [v for k,v in constants.__dict__.items() if k.startswith('ELEMENT')]

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


        for endpoint in ('runs', 'lanes', 'run_elements', 'unexpected_barcodes', 'projects', 'samples',
                         'analysis_driver_procs', 'analysis_driver_stages', 'actions'):
            resolve_dict_value_in_constant(schema[endpoint])

        expected_not_in_constant = [
            'action_id', 'action_info', 'action_type', 'analysis_driver_proc', 'best_matching_samples', 'data_deleted',
            'data_source', 'dataset_name', 'dataset_type', 'date_finished', 'date_started', 'end_date', 'exit_status',
            'files_delivered', 'files_downloaded', 'gender_genotype', 'name', 'pid', 'pipeline_used', 'sample_pipeline',
            'stage_id', 'stage_name', 'stages', 'start_date', 'started_by', 'toolset_type', 'toolset_version',
            'useable_reviewer'
        ]
        assert sorted(list_values_not_in_constants) == expected_not_in_constant

        in_constants_not_in_schema = set(self.constant_values).difference(list_values_in_constants)
        assert sorted(in_constants_not_in_schema) == ['Nb secondary alignments', 'project', 'samtools_median_coverage']
