__author__ = 'mwham'


def _format_order(query):
    if query.startswith('-'):
        return {query.lstrip('-'): -1}
    else:
        return {query: 1}


def run_elements_by_lane(run_id, query_args):
    return [
        {
            '$match': {
                'run_id': run_id
            }
        },
        {
            '$project': {
                'lane': '$lane',
                'passing_filter_reads': '$passing_filter_reads',
                'pc_pass_filter': '$pc_pass_filter',
                'yield_in_gb': '$yield_in_gb',
                'pc_q30': {'$divide': [{'$add': ['$pc_q30_r1', '$pc_q30_r2']}, 2]},
                'pc_q30_r1': '$pc_q30_r1',
                'pc_q30_r2': '$pc_q30_r2'}
        },
        {
            '$group': {
                '_id': '$lane',
                'passing_filter_reads': {'$sum': '$passing_filter_reads'},
                'pc_pass_filter': {'$avg': '$pc_pass_filter'},
                'yield_in_gb': {'$sum': '$yield_in_gb'},
                'pc_q30': {'$avg': '$pc_q30'},
                'pc_q30_r1': {'$avg': '$pc_q30_r1'},
                'pc_q30_r2': {'$avg': '$pc_q30_r2'},
                'stdev_pf': {'$stdDevSamp': '$passing_filter_reads'},
                'avg_pf': {'$avg': '$passing_filter_reads'}
            }
        },
        {
            '$project': {
                'lane': '$_id',
                'passing_filter_reads': '$passing_filter_reads',
                'pc_pass_filter': '$pc_pass_filter',
                'yield_in_gb': '$yield_in_gb',
                'pc_q30': '$pc_q30',
                'pc_q30_r1': '$pc_q30_r1',
                'pc_q30_r2': '$pc_q30_r2',
                'cv': {'$divide': ['$stdev_pf', '$avg_pf']}
            }
        },
        {
            '$sort': _format_order(query_args.get('sort', 'lane'))
        }
    ]

def run_lanes(run_id):
    return [
        {
            '$match': {'run_id': run_id}
        },
        {
            '$group': {'_id': '$lane'}
        },
        {
            '$sort': {'_id': 1}
        }
    ]

run_ids = [
    {
        '$group': {'_id': '$run_id'}
    }
]

project_ids = [
    {
        '$group': {'_id': '$project'}
    }
]
