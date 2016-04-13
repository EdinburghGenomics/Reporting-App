from tests.test_rest_api.test_aggregation import TestAggregation, FakeRequest
from unittest.mock import patch
from collections import defaultdict
from unittest.mock import Mock


class FakeMongoClient(Mock):
    def __init__(self, host, port):
        super().__init__()
        self.host, self.port = host, port
        self.dbs = defaultdict(str)

    def __getitem__(self, item):
        return self.dbs[item]


with patch('pymongo.MongoClient', new=FakeMongoClient):
    from rest_api.aggregation import database_side
    import rest_api.aggregation.database_side.stages as stages


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
        assert stages.lookup('run_elements', 'run_id', embed_as='embedded_run_elements') == exp

    def test_order(self):
        exp = {'$sort': {'sort_col': -1}}
        assert stages.order('-sort_col') == exp
        exp = {'$sort': {'sort_col': 1}}
        assert stages.order('sort_col') == exp

    def test_add(self):
        assert stages.add('$this', '$that', '$other') == {'$add': ['$this', '$that', '$other']}

    def test_divide(self):
        exp = {
            '$cond': {
                'if': {'$eq': ['$denom_col', 0]},
                'then': 0,
                'else': {'$divide': ['$num_col', '$denom_col']}
            }
        }
        assert stages.divide('$num_col', '$denom_col') == exp

    def test_percentage(self):
        exp = {
            '$cond': {
                'if': {'$eq': ['$denom_col', 0]},
                'then': 0,
                'else': {'$multiply': [{'$divide': ['$num_col', '$denom_col']}, 100]}
            }
        }
        assert stages.percentage('$num_col', '$denom_col') == exp

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
                    'analysis_driver_procs._created': 1
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
            }
        ]
        obs = stages.merge_analysis_driver_procs('id_field', projection=('this', 'that', 'other'))
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
    with patch('rest_api.aggregation.database_side.queries.request', new=fake_request):
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
