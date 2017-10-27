import pymongo
from rest_api.aggregation.server_side.expressions import *
from config import rest_config as cfg

cli = pymongo.MongoClient(cfg['db_host'], cfg['db_port'])
db = cli[cfg['db_name']]


class DataRelation:
    """
    Represents a sub-element containing data to be aggregated in a super-element
    """
    aggregated_fields = []
    endpoint = None
    id_field = None

    def __init__(self, data):
        self.data = data

    @property
    def subelements(self):
        return {}

    @property
    def superelements(self):
        return {}

    @staticmethod
    def _get_relations(endpoint, where):
        cls = data_relations[endpoint]
        return [cls(d) for d in db[endpoint].find(where) if d]

    @staticmethod
    def _get_relation(endpoint, where):
        d = db[endpoint].find_one(where)
        if d:
            return data_relations[endpoint](d)

    def _embed(self):
        for k, v in self.subelements.items():
            rels = self._get_relations(k, v)
            self.data[k] = [r.data for r in rels]

    def _trigger_superelement_aggregation(self):
        for k, v in self.superelements.items():
            rel = self._get_relation(k, v)
            if rel:
                rel.aggregate()

    def aggregate(self):
        self._embed()
        if self.aggregated_fields:
            self.data['aggregated'] = {}
            for stage in self.aggregated_fields:
                new_data = resolve(stage, self.data)
                self.data['aggregated'].update(new_data)

            db[self.endpoint].update_one(
                {self.id_field: self.data[self.id_field]},
                {'$set': {'aggregated': self.data['aggregated']}}
            )

        self._trigger_superelement_aggregation()


base_and_read_counts = {
    'bases_r1': Total('run_elements.bases_r1'),
    'bases_r2': Total('run_elements.bases_r2'),
    'q30_bases_r1': Total('run_elements.q30_bases_r1'),
    'q30_bases_r2': Total('run_elements.q30_bases_r2'),
    'clean_bases_r1': Total('run_elements.clean_bases_r1'),
    'clean_bases_r2': Total('run_elements.clean_bases_r2'),
    'clean_q30_bases_r1': Total('run_elements.clean_q30_bases_r1'),
    'clean_q30_bases_r2': Total('run_elements.clean_q30_bases_r2'),
    'total_reads': Total('run_elements.total_reads'),
    'passing_filter_reads': Total('run_elements.passing_filter_reads'),
    'clean_reads': Total('run_elements.clean_reads'),
    'run_ids': Concatenate('run_elements.run_id')
}


# = was in database-side aggregation, but not server-side
yields_and_percentages = {
    'pc_pass_filter': Percentage('aggregated.passing_filter_reads', 'aggregated.total_reads'),
    'pc_q30_r1': Percentage('aggregated.q30_bases_r1', 'aggregated.bases_r1'),
    'pc_q30_r2': Percentage('aggregated.q30_bases_r2', 'aggregated.bases_r2'),
    'pc_q30': Percentage(Add('aggregated.q30_bases_r1', 'aggregated.q30_bases_r2'), Add('aggregated.bases_r1', 'aggregated.bases_r2')),
    'yield_in_gb': Divide(Add('aggregated.bases_r1', 'aggregated.bases_r2'), Constant(1000000000)),
    'yield_q30_in_gb': Divide(Add('aggregated.q30_bases_r1', 'aggregated.q30_bases_r2'), Constant(1000000000)),  #
    'clean_yield_in_gb': Divide(Add('aggregated.clean_bases_r1', 'aggregated.clean_bases_r2'), Constant(1000000000)),  #
    'clean_yield_q30_in_gb': Divide(Add('aggregated.clean_q30_bases_r1', 'aggregated.clean_q30_bases_r2'), Constant(1000000000)),  #
    'clean_pc_q30_r1': Percentage('aggregated.clean_q30_bases_r1', 'aggregated.clean_bases_r1'),  #
    'clean_pc_q30_r2': Percentage('aggregated.clean_q30_bases_r2', 'aggregated.clean_bases_r2'),  #
    'clean_pc_q30': Percentage(Add('aggregated.clean_q30_bases_r1', 'aggregated.clean_q30_bases_r2'), Add('aggregated.clean_bases_r1', 'aggregated.clean_bases_r2'))  #
}


class RunElement(DataRelation):
    endpoint = 'run_elements'
    id_field = 'run_element_id'
    aggregated_fields = [
        {
            'pc_pass_filter': Percentage('passing_filter_reads', 'total_reads'),
            'pc_q30_r1': Percentage('q30_bases_r1', 'bases_r1'),
            'pc_q30_r2': Percentage('q30_bases_r2', 'bases_r2'),
            'pc_q30': Percentage(Add('q30_bases_r1', 'q30_bases_r2'), Add('bases_r1', 'bases_r2')),
            'yield_in_gb': Divide(Add('bases_r1', 'bases_r2'), Constant(1000000000)),
            'yield_q30_in_gb': Divide(Add('q30_bases_r1', 'q30_bases_r2'), Constant(1000000000)),  #
            'clean_yield_in_gb': Divide(Add('clean_bases_r1', 'clean_bases_r2'), Constant(1000000000)),  #
            'clean_yield_q30_in_gb': Divide(Add('clean_q30_bases_r1', 'clean_q30_bases_r2'), Constant(1000000000)),  #
            'clean_pc_q30_r1': Percentage('clean_q30_bases_r1', 'clean_bases_r1'),  #
            'clean_pc_q30_r2': Percentage('clean_q30_bases_r2', 'clean_bases_r2'),  #
            'clean_pc_q30': Percentage(Add('clean_q30_bases_r1', 'clean_q30_bases_r2'), Add('clean_bases_r1', 'clean_bases_r2'))  #
        }
    ]

    @property
    def superelements(self):
        return {
            'runs': {'run_id': self.data['run_id']},
            'lanes': {'run_id': self.data['run_id'], 'lane_number': self.data['lane']},
            'samples': {'sample_id': self.data['sample_id']}
        }


class Run(DataRelation):
    endpoint = 'runs'
    id_field = 'run_id'
    aggregated_fields = [
        base_and_read_counts,
        yields_and_percentages,
        {
            'project_ids': Concatenate('run_elements.project_id'),
            'review_statuses': Concatenate('run_elements.reviewed'),
            'useable_statuses': Concatenate('run_elements.useable'),

            'pc_adaptor': Percentage(  #
                Add(Total('run_elements.adaptor_bases_removed_r1'), Total('run_elements.adaptor_bases_removed_r2')),
                Add('aggregated.bases_r1', 'aggregated.bases_r2')
            ),
            'most_recent_proc': MostRecent('analysis_driver_procs')
        }
    ]

    @property
    def subelements(self):
        return {
            'run_elements': {'run_id': self.data['run_id']},
            'analysis_driver_procs': {'dataset_type': 'run', 'dataset_name': self.data['run_id']}
        }


class Lane(DataRelation):
    endpoint = 'lanes'
    id_field = 'lane_id'
    aggregated_fields = [
        base_and_read_counts,
        yields_and_percentages,
        {
            'cv': CoefficientOfVariation(
                'run_elements.passing_filter_reads',
                filter_func=lambda e: e.get('barcode') != 'unknown'
            ),

            'sample_ids': Concatenate('run_elements.sample_id'),  #
            'pc_adaptor': Percentage(  #
                Add(Total('run_elements.adaptor_bases_removed_r1'), Total('run_elements.adaptor_bases_removed_r2')),
                Add('aggregated.bases_r1', 'aggregated.bases_r2')
            ),

            'stdev_pf': StDevPop('run_elements.passing_filter_reads'),  #
            'avg_pf': Mean('run_elements.passing_filter_reads'),  #

            'lane_pc_optical_dups': FirstElement('run_elements.lane_pc_optical_dups'),  # # TODO: fix this in the schema
            'useable_statuses': Concatenate('run_elements.useable'),  #
            'review_statuses': Concatenate('run_elements.reviewed'),  #
        }
    ]

    @property
    def subelements(self):
        return {'run_elements': {'run_id': self.data['run_id'], 'lane': self.data['lane_number']}}


class Project(DataRelation):
    endpoint = 'projects'
    id_field = 'project_id'
    aggregated_fields = [
        {
            'nb_samples': NbUniqueElements('samples'),
            'nb_samples_reviewed': NbUniqueElements('samples', filter_func=lambda s: s.get('reviewed') in ('pass', 'fail')),  #
            'nb_samples_delivered': NbUniqueElements('samples', filter_func=lambda s: s.get('delivered') == 'yes'),  #
            'most_recent_proc': MostRecent('analysis_driver_procs')
        }
    ]

    @property
    def subelements(self):
        return {
            'samples': {'project_id': self.data['project_id']},
            'analysis_driver_procs': {'dataset_type': 'project', 'dataset_name': self.data['project_id']}
        }


class Sample(DataRelation):
    endpoint = 'samples'
    id_field = 'sample_id'
    aggregated_fields = [
        base_and_read_counts,
        yields_and_percentages,
        {
            'expected_yield_q30': Divide('expected_yield', Constant(1000000000)),  # # TODO: really!?
            'genotype_match': GenotypeMatch('genotype_validation'),  #
            'gender_match': SexCheck('called_gender', 'provided_gender'),  #
            'pc_mapped_reads': Percentage('mapped_reads', 'bam_file_reads'),
            'pc_properly_mapped_reads': Percentage('properly_mapped_reads', 'bam_file_reads'),
            'pc_duplicate_reads': Percentage('duplicate_reads', 'bam_file_reads'),
            'matching_species': MatchingSpecies('species_contamination'),
            'coverage_at_5X': Percentage('coverage.bases_at_coverage.bases_at_5X', 'coverage.genome_size'),
            'coverage_at_15X': Percentage('coverage.bases_at_coverage.bases_at_15X', 'coverage.genome_size'),
            'most_recent_proc': MostRecent('analysis_driver_procs')  #
        }
    ]

    @property
    def subelements(self):
        return {
            'run_elements': {'sample_id': self.data['sample_id']},
            'analysis_driver_procs': {'dataset_type': 'sample', 'dataset_name': self.data['sample_id']}
        }

    @property
    def superelements(self):
        return {'projects': {'project_id': self.data['project_id']}}


class AnalysisDriverProc(DataRelation):
    endpoint = 'analysis_driver_procs'
    id_field = 'proc_id'
    superendpoints = {
        'run': ('runs', 'run_id'),
        'sample': ('samples', 'sample_id'),
        'project': ('projects', 'project_id')
    }

    @property
    def superelements(self):
        endpoint, id_field = self.superendpoints[self.data['dataset_type']]
        return {endpoint: {id_field: self.data['dataset_name']}}


data_relations = {
    cls.endpoint: cls
    for cls in (Run, Lane, RunElement, Sample, Project, AnalysisDriverProc)
}


def post_insert_hook(resource, items):
    for i in items:
        rel = data_relations[resource](i)
        rel.aggregate()


def post_update_hook(resource, updates, original):
    rel = data_relations[resource](original)
    rel.data.update(updates)
    rel.aggregate()
