import statistics
from rest_api.aggregation.server_side.expressions import *
from rest_api.aggregation.database_side import db
from rest_api import cfg


def deep_dict_update(d, u):
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = deep_dict_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


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
                deep_dict_update(self.data['aggregated'], new_data)

            db[self.endpoint].update_one(
                {self.id_field: self.data[self.id_field]},
                {'$set': {'aggregated': self.data['aggregated']}}
            )

        self._trigger_superelement_aggregation()


# TODO: move these alongside the rest of the expressions in aggregation.server_side
class Reference(Calculation):
    def _expression(self, field):
        return field


class Mean(Accumulation):
    def _expression(self, elements):
        if elements:
            return sum(elements) / len(elements)


class FirstElement(Accumulation):
    def _expression(self, elements):
        if elements:
            return elements[0]


class StDevPop(Accumulation):
    def _expression(self, elements):
        if elements:
            return statistics.pstdev(elements)


class GenotypeMatch(Calculation):
    def _expression(self, geno_val):
        if not geno_val:
            return None
        elif geno_val['no_call_chip'] + geno_val['no_call_seq'] < 15:
            if geno_val['mismatching_snps'] < 6:
                return 'Match'
            elif geno_val['mismatching_snps'] > 5:
                return 'Mismatch'
        else:
            return 'Unknown'


class SexCheck(Calculation):
    def _expression(self, called, provided):
        if not called or not provided:
            return None
        elif called == provided:
            return called
        else:
            return 'Mismatch'


class MatchingSpecies(Calculation):
    def _expression(self, species_contam):
        return sorted(k for k, v in species_contam['contaminant_unique_mapped'].items() if v > 500)


class RequiredYield(Calculation):
    quantised_yields = cfg['available_yields']

    def _expression(self, genome_size):
        return {
            required_coverage: self._get_yield(genome_size, required_coverage)
            for required_coverage in cfg['available_coverages']
        }

    def _get_yield(self, genome_size, required_coverage):
        exact_yield = genome_size * required_coverage
        for y in sorted(self.quantised_yields):
            if y >= exact_yield:
                return y

        raise ValueError(
            'Could not resolve a required yield for %sX coverage and genome size %s' % (required_coverage, genome_size)
        )


class RequiredYieldQ30(RequiredYield):
    def _get_yield(self, genome_size, required_coverage):
        required_yield = super()._get_yield(genome_size, required_coverage)
        return self.quantised_yields[required_yield]


class MostRecent(Calculation):  # TODO: Should replace server_side.MostRecent
    def __init__(self, *args, date_field='_created'):
        self.date_field = date_field
        super().__init__(*args)

    def _expression(self, elements):
        procs = sorted(elements, key=lambda x: x.get(self.date_field))
        if procs:
            return procs[-1]


class UniqDict(Calculation):
    def __init__(self, *args, filter_func=None, key=None):
        super().__init__(*args, filter_func=filter_func)
        self.key = key

    def _expression(self, elements):
        if self.filter_func:
            elements = [e[self.key] for e in elements if self.filter_func(e)]
        else:
            elements = [e[self.key] for e in elements if e]

        return sorted(set(elements))


class NbUniqueDicts(Calculation):  # TODO: Should replace server_side.NbUniqueElements
    def __init__(self, *args, filter_func=None, key=None):
        super().__init__(*args, filter_func=filter_func)
        self.key = key

    def _expression(self, elements):
        if self.filter_func:
            elements = [e[self.key] for e in elements if self.filter_func(e)]
        else:
            elements = [e[self.key] for e in elements if e]

        return len(set(elements))


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
    'phix_reads': Total('run_elements.phix_reads'),
}


fastq_filtering = {
    'tiles_filtered': ToSet('run_elements.tiles_filtered'),
    'trim_r1': ToSet('run_elements.trim_r1'),
    'trim_r2': ToSet('run_elements.trim_r2')
}


yields_and_percentages = {
    'pc_pass_filter': Percentage('aggregated.passing_filter_reads', 'aggregated.total_reads'),
    'pc_phix': Percentage('aggregated.phix_reads', 'aggregated.passing_filter_reads'),
    'pc_q30_r1': Percentage('aggregated.q30_bases_r1', 'aggregated.bases_r1'),
    'pc_q30_r2': Percentage('aggregated.q30_bases_r2', 'aggregated.bases_r2'),
    'pc_q30': Percentage(Add('aggregated.q30_bases_r1', 'aggregated.q30_bases_r2'), Add('aggregated.bases_r1', 'aggregated.bases_r2')),
    'yield_in_gb': Divide(Add('aggregated.bases_r1', 'aggregated.bases_r2'), 1000000000),
    'yield_q30_in_gb': Divide(Add('aggregated.q30_bases_r1', 'aggregated.q30_bases_r2'), 1000000000),
    'clean_yield_in_gb': Divide(Add('aggregated.clean_bases_r1', 'aggregated.clean_bases_r2'), 1000000000),
    'clean_yield_q30_in_gb': Divide(Add('aggregated.clean_q30_bases_r1', 'aggregated.clean_q30_bases_r2'), 1000000000),
    'clean_pc_q30_r1': Percentage('aggregated.clean_q30_bases_r1', 'aggregated.clean_bases_r1'),
    'clean_pc_q30_r2': Percentage('aggregated.clean_q30_bases_r2', 'aggregated.clean_bases_r2'),
    'clean_pc_q30': Percentage(Add('aggregated.clean_q30_bases_r1', 'aggregated.clean_q30_bases_r2'), Add('aggregated.clean_bases_r1', 'aggregated.clean_bases_r2'))
}


def not_unknown_barcode(e):
    return e.get('barcode') != 'unknown'


class RunElement(DataRelation):
    endpoint = 'run_elements'
    id_field = 'run_element_id'
    aggregated_fields = [
        {
            'pc_pass_filter': Percentage('passing_filter_reads', 'total_reads'),
            'pc_phix': Percentage('phix_reads', 'passing_filter_reads'),
            'pc_q30_r1': Percentage('q30_bases_r1', 'bases_r1'),
            'pc_q30_r2': Percentage('q30_bases_r2', 'bases_r2'),
            'pc_q30': Percentage(Add('q30_bases_r1', 'q30_bases_r2'), Add('bases_r1', 'bases_r2')),
            'yield_in_gb': Divide(Add('bases_r1', 'bases_r2'), 1000000000),
            'yield_q30_in_gb': Divide(Add('q30_bases_r1', 'q30_bases_r2'), 1000000000),
            'clean_yield_in_gb': Divide(Add('clean_bases_r1', 'clean_bases_r2'), 1000000000),
            'clean_yield_q30_in_gb': Divide(Add('clean_q30_bases_r1', 'clean_q30_bases_r2'), 1000000000),
            'clean_pc_q30_r1': Percentage('clean_q30_bases_r1', 'clean_bases_r1'),
            'clean_pc_q30_r2': Percentage('clean_q30_bases_r2', 'clean_bases_r2'),
            'clean_pc_q30': Percentage(Add('clean_q30_bases_r1', 'clean_q30_bases_r2'), Add('clean_bases_r1', 'clean_bases_r2')),
            'pc_adaptor': Percentage(
                Add('adaptor_bases_removed_r1', 'adaptor_bases_removed_r2'),
                Add('bases_r1', 'bases_r2')
            ),
            'pc_mapped_reads': Percentage('mapping_metrics.mapped_reads', 'mapping_metrics.bam_file_reads'),
            'pc_duplicate_reads': Percentage('mapping_metrics.duplicate_reads', 'mapping_metrics.bam_file_reads'),
            'pc_opt_duplicate_reads': Percentage('mapping_metrics.picard_opt_dup_reads', 'mapping_metrics.bam_file_reads'),
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
        fastq_filtering,
        {
            'project_ids': ToSet('run_elements.project_id'),
            'review_statuses': ToSet('run_elements.reviewed', filter_func=not_unknown_barcode),
            'useable_statuses': ToSet('run_elements.useable', filter_func=not_unknown_barcode),
            'pc_adaptor': Percentage(
                Add(Total('run_elements.adaptor_bases_removed_r1'), Total('run_elements.adaptor_bases_removed_r2')),
                Add('aggregated.bases_r1', 'aggregated.bases_r2')
            ),
            'pc_opt_duplicate_reads': Percentage(
                Total('run_elements.mapping_metrics.picard_opt_dup_reads'),
                Total('run_elements.mapping_metrics.bam_file_reads')
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
        fastq_filtering,
        {
            'cv': CoefficientOfVariation('run_elements.passing_filter_reads', filter_func=not_unknown_barcode),
            'sample_ids': ToSet('run_elements.sample_id'),
            'pc_adaptor': Percentage(
                Add(Total('run_elements.adaptor_bases_removed_r1'), Total('run_elements.adaptor_bases_removed_r2')),
                Add('aggregated.bases_r1', 'aggregated.bases_r2')
            ),
            'lane_pc_optical_dups': FirstElement('run_elements.lane_pc_optical_dups'),  # TODO: fix this in the schema
            'pc_duplicate_reads': Percentage('mapping_metrics.duplicate_reads', 'mapping_metrics.bam_file_reads'),
            'pc_opt_duplicate_reads': Percentage(
                Total('run_elements.mapping_metrics.picard_opt_dup_reads'),
                Total('run_elements.mapping_metrics.bam_file_reads')
            ),
            'useable_statuses': ToSet('run_elements.useable', filter_func=not_unknown_barcode),
            'review_statuses': ToSet('run_elements.reviewed', filter_func=not_unknown_barcode),
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
            'samples': UniqDict('samples', key='sample_id'),
            'samples_reviewed': UniqDict('samples', key='sample_id', filter_func=lambda s: s.get('reviewed') in ('pass', 'fail')),
            'samples_delivered': UniqDict('samples', key='sample_id', filter_func=lambda s: s.get('delivered') == 'yes'),
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
        fastq_filtering,
        {
            'run_ids': ToSet('run_elements.run_id'),
            'genotype_match': GenotypeMatch('genotype_validation'),
            'gender_match': SexCheck('called_gender', 'provided_gender'),
            'pc_mapped_reads': Percentage('mapped_reads', 'bam_file_reads'),
            'pc_properly_mapped_reads': Percentage('properly_mapped_reads', 'bam_file_reads'),
            'pc_duplicate_reads': Percentage('duplicate_reads', 'bam_file_reads'),
            'matching_species': MatchingSpecies('species_contamination'),
            'coverage_at_5X': Percentage('coverage.bases_at_coverage.bases_at_5X', 'coverage.genome_size'),
            'coverage_at_15X': Percentage('coverage.bases_at_coverage.bases_at_15X', 'coverage.genome_size'),
            'most_recent_proc': MostRecent('analysis_driver_procs')
        },
        {
            'from_run_elements': {
                'useable_run_elements': ToSet('run_elements.run_element_id'),
                'mean_coverage': Total('run_elements.coverage.mean'),
                'bam_file_reads': Total('run_elements.mapping_metrics.bam_file_reads'),
                'mapped_reads': Total('run_elements.mapping_metrics.mapped_reads'),
                'duplicate_reads': Total('run_elements.mapping_metrics.duplicate_reads'),
                'picard_dup_reads': Total('run_elements.mapping_metrics.picard_dup_reads'),
                'picard_opt_dup_reads': Total('run_elements.mapping_metrics.picard_opt_dup_reads')
            }
        },
        {
            'from_run_elements': {
                'pc_mapped_reads': Percentage('aggregated.from_run_elements.mapped_reads', 'aggregated.from_run_elements.bam_file_reads'),
                'pc_duplicate_reads': Percentage('aggregated.from_run_elements.duplicate_reads', 'aggregated.from_run_elements.bam_file_reads'),
                'pc_opt_duplicate_reads': Percentage('aggregated.from_run_elements.picard_opt_dup_reads', 'aggregated.from_run_elements.bam_file_reads'),
            }
        }
    ]

    @property
    def subelements(self):
        return {
            'run_elements': {'sample_id': self.data['sample_id'], 'useable': 'yes'},
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


class Species(DataRelation):
    endpoint = 'species'
    id_field = 'name'
    aggregated_fields = {
        'required_yield': RequiredYield('approximate_genome_size'),
        'required_yield_q30': RequiredYieldQ30('approximate_genome_size')
    }


data_relations = {
    cls.endpoint: cls
    for cls in (Run, Lane, RunElement, Sample, Project, AnalysisDriverProc)
}


def post_insert_hook(resource, items):
    if resource in data_relations:
        for i in items:
            rel = data_relations[resource](i)
            rel.aggregate()


def post_update_hook(resource, updates, original):
    if resource in data_relations:
        rel = data_relations[resource](original)
        rel.data.update(updates)
        rel.aggregate()
