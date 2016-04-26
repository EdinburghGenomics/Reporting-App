__author__ = 'mwham'
from .expressions import *

aggregate_run_element = {
    'pc_pass_filter': Percentage('passing_filter_reads', 'total_reads'),
    'pc_q30_r1': Percentage('q30_bases_r1', 'bases_r1'),
    'pc_q30_r2': Percentage('q30_bases_r2', 'bases_r2'),
    'pc_q30': Percentage(Add('q30_bases_r1', 'q30_bases_r2'), Add('bases_r1', 'bases_r2')),
    'yield_in_gb': Divide(Add('bases_r1', 'bases_r2'), Constant(1000000000))
}

aggregate_sample = {
    'pc_pass_filter': Percentage('passing_filter_reads', 'total_reads'),
    'clean_pc_q30_r1': Percentage('clean_q30_bases_r1', 'clean_bases_r1'),
    'clean_pc_q30_r2': Percentage('clean_q30_bases_r2', 'clean_bases_r2'),
    'clean_pc_q30': Percentage(Add('clean_q30_bases_r1', 'clean_q30_bases_r2'), Add('clean_bases_r1', 'clean_bases_r2')),
    'clean_yield_in_gb': Divide(Add('clean_bases_r1', 'clean_bases_r2'), Constant(1000000000)),
    'clean_yield_q30': Divide(Add('clean_q30_bases_r1', 'clean_q30_bases_r2'), Constant(1000000000)),
    'pc_mapped_reads': Percentage('mapped_reads', 'bam_file_reads'),
    'pc_properly_mapped_reads': Percentage('properly_mapped_reads', 'bam_file_reads'),
    'pc_duplicate_reads': Percentage('duplicate_reads', 'bam_file_reads'),
    'called_gender': 'called_gender',
    'provided_gender': 'provided_gender'
}

aggregate_lane = {
    'pc_q30_r1': Percentage('q30_bases_r1', 'bases_r1'),
    'pc_q30_r2': Percentage('q30_bases_r2', 'bases_r2'),
    'pc_q30': Percentage(Add('q30_bases_r1', 'q30_bases_r2'), Add('bases_r1', 'bases_r2')),
    'pc_pass_filter': Percentage('passing_filter_reads', 'total_reads'),
    'yield_in_gb': Divide(Add('bases_r1', 'bases_r2'), Constant(1000000000)),
    'cv': CoefficientOfVariation('run_elements.passing_filter_reads', filter_func=lambda x: x.get('barcode') != 'unknown')
}

aggregate_run = {
    'pc_q30_r1': Percentage('q30_bases_r1', 'bases_r1'),
    'pc_q30_r2': Percentage('q30_bases_r2', 'bases_r2'),
    'pc_q30': Percentage(Add('q30_bases_r1', 'q30_bases_r2'), Add('bases_r1', 'bases_r2')),
    # 'pc_pass_filter': Percentage('passing_filter_reads', 'total_reads'),
    'project_ids': Concatenate('run_elements.project_id'),
    'yield_in_gb': Divide(Add('bases_r1', 'bases_r2'), Constant(1000000000)),
    'yield_q30_in_gb': Divide(Add('q30_bases_r1', 'q30_bases_r2'), Constant(1000000000)),
    'clean_yield_in_gb': Divide(Add('clean_bases_r1', 'clean_bases_r2'), Constant(1000000000)),
    'clean_yield_q30_in_gb': Divide(Add('clean_q30_bases_r1', 'clean_q30_bases_r2'), Constant(1000000000)),
    'review_statuses': Concatenate('run_elements.reviewed'),
    'useable_statuses': Concatenate('run_elements.useable')
}

aggregate_project = {
    'nb_samples': NbUniqueElements('samples')
}

aggregate_embedded_run_elements = {  # multi-element
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
    # 'project_ids': Concatenate('project_id')
}

aggregate_embedded_proc = {  # multi-element
    'analysis_driver_proc': MostRecent('analysis_driver_procs')
}

