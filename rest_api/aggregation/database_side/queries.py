import datetime
from flask import request, json, current_app as app
from config import schema
from rest_api.common import convert_date
from .stages import *


run_elements_group_by_lane = [
    {
        '$group': {
            '_id': {'run_id': '$run_id', 'lane': '$lane'},
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
            'avg_pf': {'$avg': '$passing_filter_reads'},
            'adaptor_bases_removed_r1' : {'$sum': '$adaptor_bases_removed_r1'},
            'adaptor_bases_removed_r2' : {'$sum': '$adaptor_bases_removed_r2'},
            'tiles_filtered': {'$addToSet': '$tiles_filtered'},
            'trim_r1': {'$addToSet': '$trim_r1'},
            'trim_r2': {'$addToSet': '$trim_r2'}
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
            'clean_pc_q30': percentage(
                {'$add': ['$clean_q30_bases_r1', '$clean_q30_bases_r2']},
                {'$add': ['$clean_bases_r1', '$clean_bases_r2']}
            ),
            'pc_adapter': percentage(
                {'$add': ['$adaptor_bases_removed_r1', '$adaptor_bases_removed_r2']},
                {'$add': ['$bases_r1', '$bases_r2']}
            ),
            'pc_q30_r1': percentage('$q30_bases_r1', '$bases_r1'),
            'pc_q30_r2': percentage('$q30_bases_r2', '$bases_r2'),
            'clean_pc_q30_r1': percentage('$clean_q30_bases_r1', '$clean_bases_r1'),
            'clean_pc_q30_r2': percentage('$clean_q30_bases_r2', '$clean_bases_r2'),
            'stdev_pf': '$stdev_pf',
            'avg_pf': '$avg_pf',
            'cv': divide('$stdev_pf', '$avg_pf'),
            'lane_pc_optical_dups': '$lane_pc_optical_dups',
            'useable_statuses': '$useable_statuses',
            'review_statuses': '$review_statuses',
            'tiles_filtered': '$tiles_filtered',
            'trim_r1': '$trim_r1',
            'trim_r2': '$trim_r2'
        }
    }
]


demultiplexing = [
    {
        '$project': {
            'run_element_id': '$run_element_id',
            'run_id': '$run_id',
            'barcode': '$barcode',
            'lane_number': '$lane',
            'project_id': '$project_id',
            'sample_id': '$sample_id',
            'passing_filter_reads': '$passing_filter_reads',
            'reviewed': '$reviewed',
            'useable': '$useable',
            'tiles_filtered': '$tiles_filtered',
            'trim_r1': '$trim_r1',
            'trim_r2': '$trim_r2',
            'pc_pass_filter': percentage('$passing_filter_reads', '$total_reads'),
            'pc_q30_r1': percentage('$q30_bases_r1', '$bases_r1'),
            'pc_q30_r2': percentage('$q30_bases_r2', '$bases_r2'),
            'pc_q30': percentage(add('$q30_bases_r1', '$q30_bases_r2'), add('$bases_r1', '$bases_r2')),
            'clean_pc_q30_r1': percentage('$clean_q30_bases_r1', '$clean_bases_r1'),
            'clean_pc_q30_r2': percentage('$clean_q30_bases_r2', '$clean_bases_r2'),
            'clean_pc_q30': percentage(
                add('$clean_q30_bases_r1', '$clean_q30_bases_r2'),
                add('$clean_bases_r1', '$clean_bases_r2'),
            ),
            'pc_adapter': percentage(add('$adaptor_bases_removed_r1', '$adaptor_bases_removed_r2'), add('$bases_r1', '$bases_r2')),
            'lane_pc_optical_dups': '$lane_pc_optical_dups',
            'yield_in_gb': divide(add('$bases_r1', '$bases_r2'), 1000000000),
            'clean_yield_in_gb': divide(add('$clean_bases_r1', '$clean_bases_r2'), 1000000000),
            'yield_q30_in_gb': divide(add('$q30_bases_r1', '$q30_bases_r2'), 1000000000),
            'clean_yield_q30_in_gb': divide(add('$clean_q30_bases_r1', '$clean_q30_bases_r2'), 1000000000)
        }
    }
]


sequencing_run_information = merge_analysis_driver_procs('run_id', ['run_id', 'number_of_lanes']) + [
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
            'adaptor_bases_removed_r1' : {'$sum': '$run_elements.adaptor_bases_removed_r1'},
            'adaptor_bases_removed_r2' : {'$sum': '$run_elements.adaptor_bases_removed_r2'},

            'reviewed': '$run_elements.reviewed',
            'useable': '$run_elements.useable',
            'proc_status': '$most_recent_proc.status',
            'most_recent_proc': '$most_recent_proc',
            'tiles_filtered': '$run_elements.tiles_filtered',
            'trim_r1': '$run_elements.trim_r1',
            'trim_r2': '$run_elements.trim_r2'
        }
    },
    {
        '$project': {
            'run_id': '$run_id',
            'pc_q30_r1': percentage('$q30_bases_r1', '$bases_r1'),
            'pc_q30_r2': percentage('$q30_bases_r2', '$bases_r2'),
            'pc_q30': percentage(add('$q30_bases_r1', '$q30_bases_r2'), add('$bases_r1', '$bases_r2')),
            'pc_adapter': percentage(add('$adaptor_bases_removed_r1', '$adaptor_bases_removed_r2'), add('$bases_r1', '$bases_r2')),
            'clean_pc_q30_r1': percentage('$clean_q30_bases_r1', '$clean_bases_r1'),
            'clean_pc_q30_r2': percentage('$clean_q30_bases_r2', '$clean_bases_r2'),
            'clean_pc_q30': percentage(
                add('$clean_q30_bases_r1', '$clean_q30_bases_r2'),
                add('$clean_bases_r1', '$clean_bases_r2'),
            ),
            'project_ids': '$projects',
            'yield_in_gb': divide(add('$bases_r1', '$bases_r2'), 1000000000),
            'yield_q30_in_gb': divide(add('$q30_bases_r1', '$q30_bases_r2'), 1000000000),
            'clean_yield_in_gb': divide(add('$clean_bases_r1', '$clean_bases_r2'), 1000000000),
            'clean_yield_q30_in_gb': divide(add('$clean_q30_bases_r1', '$clean_q30_bases_r2'), 1000000000),
            'review_statuses': '$reviewed',
            'useable_statuses': '$useable',
            'proc_status': '$proc_status',
            'most_recent_proc': '$most_recent_proc',
            'tiles_filtered': '$tiles_filtered',
            'trim_r1': '$trim_r1',
            'trim_r2': '$trim_r2'
        }
    }
]

sample = merge_analysis_driver_procs(
    'sample_id',
    ['sample_id', 'number_of_lanes', 'project_id', 'sample_id', 'library_id', 'user_sample_id',
     'species_name', 'expected_yield', 'expected_coverage', 'bam_file_reads', 'mapped_reads',
     'properly_mapped_reads', 'duplicate_reads', 'median_coverage', 'coverage', 'genotype_validation',
     'called_gender', 'provided_gender', 'sample_contamination', 'species_contamination', 'reviewed', 'useable',
     'delivered', 'review_comments']
) + [
    lookup('run_elements', 'sample_id'),
    {
        '$project': {
            'project_id': '$project_id',
            'sample_id': '$sample_id',
            'library_id': '$library_id',
            'user_sample_id': '$user_sample_id',
            'species_name': '$species_name',
            'expected_coverage': '$expected_coverage',
            'expected_yield': '$expected_yield',
            'bam_file_reads': '$bam_file_reads',
            'mapped_reads': '$mapped_reads',
            'properly_mapped_reads': '$properly_mapped_reads',
            'duplicate_reads': '$duplicate_reads',
            'median_coverage': '$median_coverage',
            'coverage': '$coverage',
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
            'all_run_elements': '$run_elements',
            'run_elements': {
                '$filter': {
                    'input': '$run_elements',
                    'as': 're',
                    'cond': {'$eq': ['$$re.useable', 'yes']}
                }
            }
        }
    },
    {
        '$project': {
            'project_id': '$project_id',
            'sample_id': '$sample_id',
            'library_id': '$library_id',
            'user_sample_id': '$user_sample_id',
            'species_name': '$species_name',
            'expected_yield': '$expected_yield',
            'expected_coverage': '$expected_coverage',
            'bam_file_reads': '$bam_file_reads',
            'mapped_reads': '$mapped_reads',
            'properly_mapped_reads': '$properly_mapped_reads',
            'duplicate_reads': '$duplicate_reads',
            'median_coverage': '$median_coverage',
            'coverage': '$coverage',
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
            'all_run_ids': '$run_elements.run_id',
            'run_elements': '$run_elements.run_element_id',
            'tiles_filtered': '$run_elements.tiles_filtered',
            'trim_r1': '$run_elements.trim_r1',
            'trim_r2': '$run_elements.trim_r2'
        }
    },
    {
        '$project': {
            'project_id': '$project_id',
            'sample_id': '$sample_id',
            'library_id': '$library_id',
            'user_sample_id': '$user_sample_id',
            'species_name': '$species_name',
            'expected_yield_q30': divide('$expected_yield', 1000000000),
            'expected_coverage': '$expected_coverage',
            'run_ids': '$run_ids',
            'all_run_ids': '$all_run_ids',
            'run_elements': '$run_elements',
            'bam_file_reads': '$bam_file_reads',
            'mapped_reads': '$mapped_reads',
            'properly_mapped_reads': '$properly_mapped_reads',
            'duplicate_reads': '$duplicate_reads',
            'median_coverage': '$median_coverage',
            'coverage': '$coverage',
            'genotype_match': if_else(
                eq('$genotype_validation', None),
                None,
                and_(
                    lt('$genotype_validation.mismatching_snps', 6),
                    lt(add('$genotype_validation.no_call_chip', '$genotype_validation.no_call_seq'), 15)
                ),
                'Match',
                and_(
                    gt('$genotype_validation.mismatching_snps', 5),
                    lt(add('$genotype_validation.no_call_chip', '$genotype_validation.no_call_seq'), 15)
                ),
                'Mismatch',
                else_='Unknown'
            ),
            'genotype_validation': '$genotype_validation',
            'called_gender': '$called_gender',
            'provided_gender': '$provided_gender',
            'sample_contamination': '$sample_contamination',
            'species_contamination': '$species_contamination',
            'gender_match': cond(eq('$called_gender', '$provided_gender'), '$called_gender', 'Mismatch'),
            'reviewed': '$reviewed',
            'useable': '$useable',
            'delivered': '$delivered',
            'proc_status': '$proc_status',
            'review_comments': '$review_comments',
            'most_recent_proc': '$most_recent_proc',

            'pc_pass_filter': percentage('$passing_filter_reads', '$total_reads'),
            'clean_pc_q30_r1': percentage('$clean_q30_bases_r1', '$clean_bases_r1'),
            'clean_pc_q30_r2': percentage('$clean_q30_bases_r2', '$clean_bases_r2'),
            'clean_pc_q30': percentage(
                add('$clean_q30_bases_r1', '$clean_q30_bases_r2'),
                add('$clean_bases_r1', '$clean_bases_r2')),
            'clean_yield_in_gb': divide(add('$clean_bases_r1', '$clean_bases_r2'), 1000000000),
            'clean_yield_q30': divide(add('$clean_q30_bases_r1', '$clean_q30_bases_r2'), 1000000000),
            'pc_mapped_reads': percentage('$mapped_reads', '$bam_file_reads'),
            'pc_properly_mapped_reads': percentage('$properly_mapped_reads', '$bam_file_reads'),
            'pc_duplicate_reads': percentage('$duplicate_reads', '$bam_file_reads'),
            'tiles_filtered': '$tiles_filtered',
            'trim_r1': '$trim_r1',
            'trim_r2': '$trim_r2'
        }
    }
]


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
                       'input': '$samples',
                       'as': 'sample',
                       'cond': or_(
                           eq('$$sample.reviewed', 'pass'),
                           eq('$$sample.reviewed', 'fail')
                       )
                    }
                }
            },
            'nb_samples_delivered': {
                '$size': {
                    '$filter': {
                       'input': '$samples',
                       'as': 'sample',
                       'cond': eq('$$sample.delivered', 'yes')
                    }
                }
            }
        }
    }
]


def resolve_pipeline(endpoint, base_pipeline):
    pipeline = []
    schema_endpoint = list(schema[endpoint])
    schema_endpoint.append(app.config['DATE_CREATED'])
    schema_endpoint.append(app.config['LAST_UPDATED'])
    sort_col = request.args.get('sort', list(schema_endpoint)[0])
    match = json.loads(request.args.get('match', '{}'))
    or_match = match.pop('$or', None)  # TODO: make complex matches generic
    if or_match:
        multi_match_col = list(or_match[0])[0]  # get one of the field names in the or statement
        match[multi_match_col] = or_(*or_match)
    orderer = order(sort_col)
    sorting_done = False

    for k in schema_endpoint:
        if k in match:
            pipeline.append({'$match': convert_date(resolve_match(k, match.pop(k)))})
        if not sorting_done and k == sort_col.lstrip('-'):
            pipeline.append(orderer)
            sorting_done = True

    for stage in base_pipeline:
        pipeline.append(stage)

        for k in stage.get('$project', {}):
            if k in [col.lstrip('$') for col in match]:
                pipeline.append({'$match': convert_date(resolve_match(k, match.pop(k)))})
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
