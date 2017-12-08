from os.path import join
from tests.test_rest_api import TestBase


class TestAggregation(TestBase):
    def _json_test_file(self, pre_or_post, filename):
        return open(join(self.assets_dir, 'json', pre_or_post + '_aggregation', filename))

    def _compare_jsons(self, o, e):
        for x in (o, e):
            for y in ('run_ids',):
                self._reorder_comma_sep_list(x['data'], y)

        if o != e:
            print('!o_eq_e')
            for x, y in zip(e['data'], o['data']):
                missing = [k for k in x if k not in y]
                if missing:
                    print('missing expected key:')
                    print(missing)
            for x, y in zip(e['data'], o['data']):
                unexpected = [k for k in y if k not in x]
                if unexpected:
                    print('unexpected key:')
                    print(unexpected)
            for x, y in zip(e['data'], o['data']):
                different_values = [
                    '%s: %s != %s' % (k, x[k], y[k])
                    for k in set(x).intersection(set(y))
                    if x[k] != y[k]
                ]
                if different_values:
                    print('different values:')
                    print(different_values)
            raise AssertionError

    @staticmethod
    def _reorder_comma_sep_list(data, key):
        for e in data:
            if key not in e:
                continue
            if type(e[key]) is list:
                e[key] = list(sorted(e[key]))


class FakeRequest:
    def __init__(self, args):
        self.args = args
