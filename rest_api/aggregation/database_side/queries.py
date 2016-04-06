from flask import request, json
from config import schema
from .stages import *


run_elements_by_lane = [
    {
        '$project': {
            'lane': '$lane',
            'total_reads': '$total_reads',
            'passing_filter_reads': '$passing_filter_reads',
            'yield_in_gb': '$yield_in_gb',
            'bases_r1': '$bases_r1',
            'q30_bases_r1': '$q30_bases_r1',
            'bases_r2': '$bases_r2',
            'q30_bases_r2': '$q30_bases_r2'
        }
    },
    {
        '$group': {
            '_id': '$lane',
            'total_reads': {'$sum': '$total_reads'},
            'passing_filter_reads': {'$sum': '$passing_filter_reads'},

            'bases_r1': {'$sum': '$bases_r1'},
            'q30_bases_r1': {'$sum': '$q30_bases_r1'},
            'bases_r2': {'$sum': '$bases_r2'},
            'q30_bases_r2': {'$sum': '$q30_bases_r2'},

            'stdev_pf': {'$stdDevPop': '$passing_filter_reads'},
            'avg_pf': {'$avg': '$passing_filter_reads'}
        }
    },
    {
        '$project': {
            'lane_number': '$_id',
            'passing_filter_reads': '$passing_filter_reads',
            'pc_pass_filter': percentage('$passing_filter_reads', '$total_reads'),
            'yield_in_gb': divide('$total_reads', 1000000000),
            'pc_q30': percentage(
                {'$add': ['$q30_bases_r1', '$q30_bases_r2']},
                {'$add': ['$bases_r1', '$bases_r2']}
            ),
            'pc_q30_r1': percentage('$q30_bases_r1', '$bases_r1'),
            'pc_q30_r2': percentage('$q30_bases_r2', '$bases_r2'),
            'stdev_pf': '$stdev_pf',
            'avg_pf': '$avg_pf',
            'cv': divide('$stdev_pf', '$avg_pf')
        }
    }
]


sequencing_run_information = [
    lookup('run_elements', 'run_id'),
    lookup('analysis_driver_procs', 'most_recent_proc_id', 'proc_id', 'most_recent_proc'),
    {
        '$project': {
            'run_id': '$run_id',
            'projects': '$run_elements.project_id',

            'bases_r1': {'$sum': '$run_elements.bases_r1'},
            'q30_bases_r1': {'$sum': '$run_elements.q30_bases_r1'},
            'bases_r2': {'$sum': '$run_elements.bases_r2'},
            'q30_bases_r2': {'$sum': '$run_elements.q30_bases_r2'},

            'clean_bases_r1': {'$sum': '$run_elements.clean_bases_r1'},
            'clean_bases_r2': {'$sum': '$run_elements.clean_bases_r2'},
            'clean_q30_bases_r1': {'$sum': '$run_elements.clean_q30_bases_r1'},
            'clean_q30_bases_r2': {'$sum': '$run_elements.clean_q30_bases_r2'},

            'reviewed': '$run_elements.reviewed',
            'useable': '$run_elements.useable',
            'most_recent_proc': '$most_recent_proc'
        }
    },
    {
        '$project': {
            'run_id': '$run_id',
            'pc_q30_r1': percentage('$q30_bases_r1', '$bases_r1'),
            'pc_q30_r2': percentage('$q30_bases_r2', '$bases_r2'),
            'pc_q30': percentage(add('$q30_bases_r1', '$q30_bases_r2'), add('$bases_r1', '$bases_r2')),
            # 'pc_pass_filter': Percentage('passing_filter_reads', 'total_reads'),
            'project_ids': '$projects',
            'yield_in_gb': divide(add('$bases_r1', '$bases_r2'), 1000000000),
            'yield_q30_in_gb': divide(add('$q30_bases_r1', '$q30_bases_r2'), 1000000000),
            'clean_yield_in_gb': divide(add('$clean_bases_r1', '$clean_bases_r2'), 1000000000),
            'clean_yield_q30_in_gb': divide(add('$clean_q30_bases_r1', '$clean_q30_bases_r2'), 1000000000),
            'review_statuses': '$reviewed',
            'useable_statuses': '$useable',
            'most_recent_proc': '$most_recent_proc'
        }
    }
]


demultiplexing = [
    {
        '$project': {
            'barcode': '$barcode',
            'project_id': '$project_id',
            'sample_id': '$sample_id',
            'passing_filter_reads': '$passing_filter_reads',
            'reviewed': '$reviewed',
            'useable': '$useable',
            'pc_pass_filter': percentage('$passing_filter_reads', '$total_reads'),
            'pc_q30_r1': percentage('$q30_bases_r1', '$bases_r1'),
            'pc_q30_r2': percentage('$q30_bases_r2', '$bases_r2'),
            'pc_q30': percentage(add('$q30_bases_r1', '$q30_bases_r2'), add('$bases_r1', '$bases_r2')),
            'yield_in_gb': divide(add('$bases_r1', '$bases_r2'), 1000000000)
        }
    }
]


sample = [
    lookup('run_elements', 'sample_id'),
    {
        '$project': {
            'sample_id': '$sample_id',
            'library_id': '$library_id',
            'user_sample_id': '$user_sample_id',
            'bam_file_reads': '$bam_file_reads',
            'mapped_reads': '$mapped_reads',
            'properly_mapped_reads': '$properly_mapped_reads',
            'duplicate_reads': '$duplicate_reads',
            'median_coverage': '$median_coverage',
            'genotype_validation': '$genotype_validation',
            'reviewed': '$reviewed',
            'useable': '$useable',

            'bases_r1': {'$sum': '$run_elements.bases_r1'},
            'bases_r2': {'$sum': '$run_elements.bases_r2'},
            'q30_bases_r1': {'$sum': '$run_elements.q30_bases_r1'},
            'q30_bases_r2': {'$sum': '$run_elements.q30_bases_r2'},
            'clean_bases_r1': {'$sum': '$run_elements.clean_bases_r1'},
            'clean_bases_r2': {'$sum': '$run_elements.clean_bases_r2'},
            'clean_q30_bases_r1': {'$sum': '$run_elements.clean_q30_bases_r1'},
            'clean_q30_bases_r2': {'$sum': '$run_elements.clean_q30_bases_r2'},
            'total_reads': {'$sum': '$run_elements.total_reads'},
            'passing_filter_reads': {'$sum': '$run_elements.passing_filter_reads'},
            'clean_reads': {'$sum': '$run_elements.clean_reads'},
            'run_ids': '$run_elements.run_id'
        }
    },
    {
        '$project': {
            'sample_id': '$sample_id',
            'library_id': '$library_id',
            'user_sample_id': '$user_sample_id',
            'run_ids': '$run_ids',
            'bam_file_reads': '$bam_file_reads',
            'mapped_reads': '$mapped_reads',
            'properly_mapped_reads': '$properly_mapped_reads',
            'duplicate_reads': '$duplicate_reads',
            'median_coverage': '$median_coverage',
            'genotype_validation': '$genotype_validation',
            'reviewed': '$reviewed',
            'useable': '$useable',

            'pc_pass_filter': percentage('$passing_filter_reads', '$total_reads'),
            'clean_pc_q30_r1': percentage('$clean_q30_bases_r1', '$clean_bases_r1'),
            'clean_pc_q30_r2': percentage('$clean_q30_bases_r2', '$clean_bases_r2'),
            'clean_pc_q30': percentage(add('$clean_q30_bases_r1', '$clean_q30_bases_r2'), add('$clean_bases_r1', '$clean_bases_r2')),
            'clean_yield_in_gb': divide(add('$clean_bases_r1', '$clean_bases_r2'), 1000000000),
            'clean_yield_q30': divide(add('$clean_q30_bases_r1', '$clean_q30_bases_r2'), 1000000000),
            'pc_mapped_reads': percentage('$mapped_reads', '$bam_file_reads'),
            'pc_properly_mapped_reads': percentage('$properly_mapped_reads', '$bam_file_reads'),
            'pc_duplicate_reads': percentage('$duplicate_reads', '$bam_file_reads')
        }
    }
]


sequencing_run_information_opt = [
    lookup('run_elements', 'run_id'),
    {
        '$project': {
            'run_id': '$run_id',
            'projects': '$run_elements.project_id',

            'bases_r1': {'$sum': '$run_elements.bases_r1'},
            'q30_bases_r1': {'$sum': '$run_elements.q30_bases_r1'},
            'bases_r2': {'$sum': '$run_elements.bases_r2'},
            'q30_bases_r2': {'$sum': '$run_elements.q30_bases_r2'},

            'clean_bases_r1': {'$sum': '$run_elements.clean_bases_r1'},
            'clean_bases_r2': {'$sum': '$run_elements.clean_bases_r2'},
            'clean_q30_bases_r1': {'$sum': '$run_elements.clean_q30_bases_r1'},
            'clean_q30_bases_r2': {'$sum': '$run_elements.clean_q30_bases_r2'},

            'reviewed': '$run_elements.reviewed',
            'useable': '$run_elements.useable'
        }
    },
    lookup('analysis_driver_procs', 'most_recent_proc_id', 'proc_id', 'most_recent_proc'),
    {
        '$project': {
            'run_id': '$run_id',
            'pc_q30_r1': percentage('$q30_bases_r1', '$bases_r1'),
            'pc_q30_r2': percentage('$q30_bases_r2', '$bases_r2'),
            'pc_q30': percentage(add('$q30_bases_r1', '$q30_bases_r2'), add('$bases_r1', '$bases_r2')),
            # 'pc_pass_filter': Percentage('passing_filter_reads', 'total_reads'),
            'project_ids': '$projects',
            'yield_in_gb': divide(add('$bases_r1', '$bases_r2'), 1000000000),
            'yield_q30_in_gb': divide(add('$q30_bases_r1', '$q30_bases_r2'), 1000000000),
            'clean_yield_in_gb': divide(add('$clean_bases_r1', '$clean_bases_r2'), 1000000000),
            'clean_yield_q30_in_gb': divide(add('$clean_q30_bases_r1', '$clean_q30_bases_r2'), 1000000000),
            'review_statuses': '$reviewed',
            'useable_statuses': '$useable',
            'most_recent_proc': '$most_recent_proc'
        }
    }
]


def resolve_pipeline(endpoint, base_pipeline):
    pipeline = []
    schema_keys = schema[endpoint].keys()
    sort_col = request.args.get('sort', '')
    _paginator = paginator(
        sort_col,
        page_number=request.args.get('page', '1'),
        page_size=request.args.get('max_results', '50')
    )
    match = json.loads(request.args.get('match', '{}'))
    pagination_done = False

    for k in list(match):
        if k in schema_keys:
            pipeline.append({'$match': {k: match.pop(k)}})

    if sort_col.lstrip('-') in schema_keys:
        pipeline += _paginator
        pagination_done = True

    for stage in base_pipeline:
        pipeline.append(stage)

        if not pagination_done and sort_col.lstrip('-') in stage.get('$project', {}).keys():
            pipeline += _paginator
            pagination_done = True

        for k in list(match):
            if k in stage.get('$project', {}).keys():
                pipeline.append({'$match': {k: match.pop(k)}})

    return pipeline
