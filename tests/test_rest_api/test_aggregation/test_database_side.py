from tests.test_rest_api.test_aggregation import TestAggregation, FakeRequest
from unittest.mock import Mock, patch
from rest_api.aggregation import database_side
from rest_api.aggregation.database_side import stages as s


class FakeMongoClient(Mock):
    def __init__(self, host, port):
        super().__init__()
        self.host, self.port = host, port
        collection = FakeCollection(
            [
                {'this': None, 'that': None, 'other': None},
                {'this': None, 'that': None, 'other': None}
            ]
        )
        self.db = {'test_db': FakeDatabase(test_endpoint=collection)}

    def __getitem__(self, item):
        return self.db[item]


class FakeDatabase:
    def __init__(self, **collections):
        self.collections = collections

    def __getitem__(self, item):
        return self.collections[item]


class FakeCollection:
    def __init__(self, data):
        self.data = data

    def aggregate(self, pipeline):
        return self.data


fake_data = [
    {'this': None, 'that': None, 'other': None},
    {'this': None, 'that': None, 'other': None}
]
database_side.cli = FakeMongoClient('host', 'port')
database_side.db = database_side.cli['test_db']


class TestQueries(TestAggregation):
    pass


class TestStages(TestAggregation):
    def test_lookup(self):
        exp = {
            '$lookup': {
                'from': 'run_elements',
                'localField': 'run_id',
                'foreignField': 'run_id',
                'as': 'embedded_run_elements'
            }
        }
        assert s.lookup('run_elements', 'run_id', embed_as='embedded_run_elements') == exp

    def test_order(self):
        exp = {'$sort': {'sort_col': -1}}
        assert s.order('-sort_col') == exp
        exp = {'$sort': {'sort_col': 1}}
        assert s.order('sort_col') == exp

    def test_add(self):
        assert s.add('$this', '$that', '$other') == {'$add': ['$this', '$that', '$other']}

    def test_divide(self):
        exp = {
            '$cond': [
                {'$eq': ['$denom_col', 0]},
                0,
                {'$divide': ['$num_col', '$denom_col']}
            ]
        }
        assert s.divide('$num_col', '$denom_col') == exp

    def test_percentage(self):
        exp = {
            '$cond': [
                {'$eq': ['$denom_col', 0]},
                0,
                {'$multiply': [{'$divide': ['$num_col', '$denom_col']}, 100]}
            ]
        }
        assert s.percentage('$num_col', '$denom_col') == exp

    def test_merge_analysis_driver_procs(self):
        exp = [
            {
                '$lookup': {
                    'from': 'analysis_driver_procs',
                    'localField': 'id_field',
                    'foreignField': 'dataset_name',
                    'as': 'analysis_driver_procs'
                }
            },
            {
                '$unwind': {
                    'path': '$analysis_driver_procs',
                    'preserveNullAndEmptyArrays': True
                }
            },
            {
                '$sort': {
                    'id_field': -1,
                    'analysis_driver_procs._created': -1
                }
            },
            {
                '$group': {
                    '_id': '$id_field',
                    'most_recent_proc': {'$first': '$analysis_driver_procs'},
                    'this': {'$first': '$this'},
                    'that': {'$first': '$that'},
                    'other': {'$first': '$other'}
                }
            },
            {
                '$lookup': {
                    'from': 'analysis_driver_stages',
                    'localField': 'most_recent_proc.proc_id',
                    'foreignField': 'analysis_driver_proc',
                    'as': 'most_recent_proc.stages'
                }
            }
        ]
        obs = s.merge_analysis_driver_procs('id_field', projection=('this', 'that', 'other'))
        assert obs == exp

    def test_if_else(self):
        obs = s.if_else(
            s.eq('$x', None),
            'X is null',
            s.eq('$x', 6),
            'X is 6',
            s.eq('$x', 5),
            'X is 5',
            else_='X is something else'
        )
        exp = s.cond(
            s.eq('$x', None),
            'X is null',
            s.cond(
                s.eq('$x', 6),
                'X is 6',
                s.cond(
                    s.eq('$x', 5),
                    'X is 5',
                    'X is something else'
                )
            )
        )
        assert obs == exp


def test_resolve_pipeline():
    fake_request = FakeRequest(
        args={
            'sort': '-this',
            'match': '{"this":1,"other":2,"$or":[{"that":0},{"that":1}]}'
        }
    )
    base_pipeline = [
        {'$project': {'this': '$sample_id', 'that': '$that'}},
        {'$project': {'this': '$this', 'that': '$that', 'other': {'$add': ['$this', '$that']}}}
    ]
    with patch('rest_api.aggregation.database_side.queries.request', new=fake_request), \
         patch('rest_api.aggregation.database_side.queries.app'):
        obs = database_side.queries.resolve_pipeline('samples', base_pipeline)

    exp = [
        {'$project': {'this': '$sample_id', 'that': '$that'}},
        {'$match': {'$or': [{'that': 0}, {'that': 1}]}},
        {'$match': {'this': 1}},
        {'$sort': {'this': -1}},
        {'$project': {'this': '$this', 'that': '$that', 'other': {'$add': ['$this', '$that']}}},
        {'$match': {'other': 2}}
    ]
    assert obs[0] == exp[0]
    for stage in obs[1:4]:
        assert stage in exp[1:4]
    assert obs[5] == exp[5]


def test_aggregate():
    patched_resolve_pipeline = patch('rest_api.aggregation.database_side.queries.resolve_pipeline')
    patched_request = patch('rest_api.aggregation.database_side.request', new=FakeRequest({}))
    patched_jsonify = patch('rest_api.aggregation.database_side.jsonify', new=dict)
    with patched_resolve_pipeline, patched_request, patched_jsonify:
        obs = database_side.aggregate(
            'test_endpoint',
            [{'a': 'test', 'aggregataion': 'pipeline'}],
            Mock(
                logger=Mock(),
                config={
                    'QUERY_PAGE': 'page',
                    'QUERY_MAX_RESULTS': 'max_results',
                    'META': '_meta',
                    'LINKS': '_links',
                    'ITEMS': 'data'
                }
            )
        )
    exp = {
        '_meta': {'total': 2},
        'data': fake_data
    }
    assert obs == exp
