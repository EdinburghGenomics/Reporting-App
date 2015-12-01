__author__ = 'mwham'


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
                'lane': '$_id',
                'passing_filter_reads': '$passing_filter_reads',
                'pc_pass_filter': {
                    '$multiply': [
                        {'$divide': ['$passing_filter_reads', '$total_reads']},
                        100
                    ]
                },
                'yield_in_gb': {
                    '$divide': [
                        '$total_reads',
                        1000000000
                    ]
                },
                'pc_q30': {
                    '$multiply': [
                        {'$divide': [
                            {'$add': ['$q30_bases_r1', '$q30_bases_r2']},
                            {'$add': ['$bases_r1', '$bases_r2']}
                        ]},
                        100
                    ]
                },
                'pc_q30_r1': {'$multiply': [{'$divide': ['$q30_bases_r1', '$bases_r1']}, 100]},
                'pc_q30_r2': {'$multiply': [{'$divide': ['$q30_bases_r2', '$bases_r2']}, 100]},
                'stdev_pf': '$stdev_pf',
                'avg_pf': '$avg_pf',
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


def _format_order(query):
    if query.startswith('-'):
        return {query.lstrip('-'): -1}
    else:
        return {query: 1}
