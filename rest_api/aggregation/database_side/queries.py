from flask import request, json
from config import schema
from .stages import *


run_elements_group_by_lane = [

    {
        '$group': {
            '_id': {'run_id': '$run_id', 'lane':'$lane'},
            'lane': {'$first': '$lane'},
            'run_id': {'$first': '$run_id'},
            'sample_ids': {'$addToSet': '$sample_id'},
            'useable_statuses': {'$addToSet': '$useable'},
            'review_statuses': {'$addToSet': '$reviewed'},
            'total_reads': {'$sum': '$total_reads'},
            'passing_filter_reads': {'$sum': '$passing_filter_reads'},

            'bases_r1': {'$sum': '$bases_r1'},
            'q30_bases_r1': {'$sum': '$q30_bases_r1'},
            'bases_r2': {'$sum': '$bases_r2'},
            'q30_bases_r2': {'$sum': '$q30_bases_r2'},
            'clean_bases_r1': {'$sum': '$clean_bases_r1'},
            'clean_bases_r2': {'$sum': '$clean_bases_r2'},
            'clean_q30_bases_r1': {'$sum': '$clean_q30_bases_r1'},
            'clean_q30_bases_r2': {'$sum': '$clean_q30_bases_r2'},
            'lane_pc_optical_dups': {'$first': '$lane_pc_optical_dups'},
            'stdev_pf': {'$stdDevPop': '$passing_filter_reads'},
            'avg_pf': {'$avg': '$passing_filter_reads'}
        }
    },
    {
        '$project': {
            'run_id': '$run_id',
            'lane_number': '$lane',
            'sample_ids': '$sample_ids',
            'passing_filter_reads': '$passing_filter_reads',
            'pc_pass_filter': percentage('$passing_filter_reads', '$total_reads'),
            'yield_in_gb': divide({'$add': ['$bases_r1', '$bases_r2']}, 1000000000),
            'yield_q30_in_gb': divide({'$add': ['$q30_bases_r1', '$q30_bases_r2']}, 1000000000),
            'clean_yield_in_gb': divide(add('$clean_bases_r1', '$clean_bases_r2'), 1000000000),
            'clean_yield_q30_in_gb': divide(add('$clean_q30_bases_r1', '$clean_q30_bases_r2'), 1000000000),
            'pc_q30': percentage(
                {'$add': ['$q30_bases_r1', '$q30_bases_r2']},
                {'$add': ['$bases_r1', '$bases_r2']}
            ),
            'pc_q30_r1': percentage('$q30_bases_r1', '$bases_r1'),
            'pc_q30_r2': percentage('$q30_bases_r2', '$bases_r2'),
            'stdev_pf': '$stdev_pf',
            'avg_pf': '$avg_pf',
            'cv': divide('$stdev_pf', '$avg_pf'),
            'lane_pc_optical_dups': '$lane_pc_optical_dups',
            'useable_statuses': '$useable_statuses',
            'review_statuses': '$review_statuses'
        }
    }
]


demultiplexing = [
    {
        '$project': {
            'run_id': '$run_id',
            'barcode': '$barcode',
            'lane_number': '$lane',
            'project_id': '$project_id',
            'sample_id': '$sample_id',
            'passing_filter_reads': '$passing_filter_reads',
            'reviewed': '$reviewed',
            'useable': '$useable',
            'pc_pass_filter': percentage('$passing_filter_reads', '$total_reads'),
            'pc_q30_r1': percentage('$q30_bases_r1', '$bases_r1'),
            'pc_q30_r2': percentage('$q30_bases_r2', '$bases_r2'),
            'pc_q30': percentage(add('$q30_bases_r1', '$q30_bases_r2'), add('$bases_r1', '$bases_r2')),
            'yield_in_gb': divide(add('$bases_r1', '$bases_r2'), 1000000000),
            'clean_yield_in_gb': divide(add('$clean_bases_r1', '$clean_bases_r2'), 1000000000),
            'yield_q30_in_gb': divide(add('$q30_bases_r1', '$q30_bases_r2'), 1000000000),
            'clean_yield_in_gb': divide(add('$clean_bases_r1', '$clean_bases_r2'), 1000000000),
            'clean_yield_q30_in_gb': divide(add('$clean_q30_bases_r1', '$clean_q30_bases_r2'), 1000000000)
        }
    }
]
sequencing_run_information = merge_analysis_driver_procs('run_id', ['run_id', 'number_of_lanes'])

sequencing_run_information.extend([
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
            'useable': '$run_elements.useable',
            'proc_status': '$most_recent_proc.status',
            'most_recent_proc': '$most_recent_proc'
        }
    },
    {
        '$project': {
            'run_id': '$run_id',
            'pc_q30_r1': percentage('$q30_bases_r1', '$bases_r1'),
            'pc_q30_r2': percentage('$q30_bases_r2', '$bases_r2'),
            'pc_q30': percentage(add('$q30_bases_r1', '$q30_bases_r2'), add('$bases_r1', '$bases_r2')),
            'project_ids': '$projects',
            'yield_in_gb': divide(add('$bases_r1', '$bases_r2'), 1000000000),
            'yield_q30_in_gb': divide(add('$q30_bases_r1', '$q30_bases_r2'), 1000000000),
            'clean_yield_in_gb': divide(add('$clean_bases_r1', '$clean_bases_r2'), 1000000000),
            'clean_yield_q30_in_gb': divide(add('$clean_q30_bases_r1', '$clean_q30_bases_r2'), 1000000000),
            'review_statuses': '$reviewed',
            'useable_statuses': '$useable',
            'proc_status': '$proc_status',
            'most_recent_proc': '$most_recent_proc'
        }
    }
])

sample = merge_analysis_driver_procs('sample_id', [
    'sample_id', 'number_of_lanes', 'project_id', 'sample_id', 'library_id', 'user_sample_id',
    'bam_file_reads', 'mapped_reads', 'properly_mapped_reads', 'duplicate_reads', 'median_coverage',
    'genotype_validation', 'called_gender', 'provided_gender', 'sample_contamination', 'species_contamination',
    'reviewed', 'useable', 'delivered', 'review_comments'])

sample.extend([
    lookup('run_elements', 'sample_id'),
    {
        '$project': {
            'project_id': '$project_id',
            'sample_id': '$sample_id',
            'library_id': '$library_id',
            'user_sample_id': '$user_sample_id',
            'bam_file_reads': '$bam_file_reads',
            'mapped_reads': '$mapped_reads',
            'properly_mapped_reads': '$properly_mapped_reads',
            'duplicate_reads': '$duplicate_reads',
            'median_coverage': '$median_coverage',
            'genotype_validation': '$genotype_validation',
            'called_gender': '$called_gender',
            'provided_gender': '$provided_gender',
            'sample_contamination': '$sample_contamination',
            'species_contamination': '$species_contamination',
            'reviewed': '$reviewed',
            'useable': '$useable',
            'delivered': '$delivered',
            'proc_status': '$most_recent_proc.status',
            'review_comments': '$review_comments',
            'most_recent_proc': '$most_recent_proc',

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
            'run_ids': '$run_elements.run_id',
            'run_elements': '$run_elements.run_element_id'
        }
    },
    {
        '$project': {
            'project_id': '$project_id',
            'sample_id': '$sample_id',
            'library_id': '$library_id',
            'user_sample_id': '$user_sample_id',
            'run_ids': '$run_ids',
            'run_elements': '$run_elements',
            'bam_file_reads': '$bam_file_reads',
            'mapped_reads': '$mapped_reads',
            'properly_mapped_reads': '$properly_mapped_reads',
            'duplicate_reads': '$duplicate_reads',
            'median_coverage': '$median_coverage',
            'genotype_match': {'$cond':
                [
                    {'$and': [
                        {'$lt': ['$genotype_validation.mismatching_snps', 6]},
                        {'$lt': [{'$add':['$genotype_validation.no_call_chip', '$genotype_validation.no_call_seq']}, 15]}
                    ]},
                    'Match',
                    {'$cond': [
                        {'$and':
                            [
                               {'$gt': ['$genotype_validation.mismatching_snps', 5]},
                               {'$lt': [{'$add':['$genotype_validation.no_call_chip', '$genotype_validation.no_call_seq']}, 15]}
                            ]
                        },
                        'Mismatch',
                        'Unknown'
                        ]
                    }
                ]

            },
            'genotype_validation': '$genotype_validation',
            'called_gender': '$called_gender',
            'provided_gender': '$provided_gender',
            'sample_contamination': '$sample_contamination',
            'species_contamination': '$species_contamination',
            'gender_match': {'$cond':
                                 [
                                     {'$eq': ['$called_gender', '$provided_gender']},
                                     '$called_gender',
                                     'Mismatch'
                                 ]
            },
            'reviewed': '$reviewed',
            'useable': '$useable',
            'delivered': '$delivered',
            'proc_status': '$proc_status',
            'review_comments': '$review_comments',
            'most_recent_proc': '$most_recent_proc',

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
])


project_info = [
    lookup('samples', 'project_id'),
    {
        '$project': {
            'project_id': '$project_id',
            '_created': '$_created',
            'nb_samples': {'$size': '$samples'},
            'nb_samples_reviewed': {
                '$size': {
                    '$filter': {
                       'input': "$samples",
                       'as': "sample",
                       'cond': {"$or": [
                           {"$eq": ["$$sample.reviewed", "pass"]},
                           {"$eq": ["$$sample.reviewed", "fail"]}
                       ]}
                    }
                }
            },
            'nb_samples_delivered': {
                '$size': {
                    '$filter': {
                       'input': "$samples",
                       'as': "sample",
                       'cond': {"$eq": ["$$sample.delivered", "yes"]}
                    }
                }
            },
        }
    }
]


def resolve_pipeline(endpoint, base_pipeline):
    pipeline = []
    schema_keys = schema[endpoint].keys()
    sort_col = request.args.get('sort', list(schema_keys)[0])
    match = json.loads(request.args.get('match', '{}'))
    or_match = match.pop('$or', None)  # TODO: make complex matches generic
    if or_match:
        multi_match_col = list(or_match[0])[0]  # get one of the field names in the or statement
        match[multi_match_col] = {'$or': or_match}
    orderer = order(sort_col)
    sorting_done = False

    for k in schema_keys:
        if k in match:
            pipeline.append({'$match': resolve_match(k, match.pop(k))})
        if not sorting_done and k == sort_col.lstrip('-'):
            pipeline.append(orderer)
            sorting_done = True

    for stage in base_pipeline:
        pipeline.append(stage)

        for k in stage.get('$project', {}):
            if k in [col.lstrip('$') for col in match]:
                pipeline.append({'$match': resolve_match(k, match.pop(k))})
            if not sorting_done and k == sort_col.lstrip('-'):
                pipeline.append(orderer)
                sorting_done = True

    if not sorting_done:
        pipeline.append(orderer)

    return pipeline


def resolve_match(key, match_value):
    if type(match_value) is dict and '$or' in match_value:
        return match_value
    else:
        return {key: match_value}
