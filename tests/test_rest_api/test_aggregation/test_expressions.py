from datetime import datetime
from math import sqrt

from rest_api.aggregation import expressions


def test_reference():
    e = expressions.Reference('this.that')
    assert e.evaluate({'this': {'that': 'other'}}) == 'other'


def test_mean():
    e = expressions.Mean('things.x')
    assert e.evaluate({'things': [{'x': x} for x in range(12)]}) == 5.5


def test_first_element():
    e = expressions.FirstElement('things.x')
    assert e.evaluate({'things': [{'x': x} for x in range(12)]}) == 0


def test_stdev_pop():
    e = expressions.StDevPop('things.x')
    vals = list(range(12))
    mean = sum(vals) / len(vals)  # 5.5
    devs = [(v - mean) * (v - mean) for v in vals]
    var = sum(devs) / len(devs)  # 11.91666...
    stdev_pop = sqrt(var)  # 3.452052529534663

    assert e.evaluate({'things': [{'x': x} for x in vals]}) == stdev_pop


def test_genotype_match():
    e = expressions.GenotypeMatch('genotyping')
    assert e.evaluate({'genotyping': {}}) is None
    assert e.evaluate({'genotyping': {'no_call_chip': 7, 'no_call_seq': 7, 'mismatching_snps': 5}}) == 'Match'
    assert e.evaluate({'genotyping': {'no_call_chip': 7, 'no_call_seq': 7, 'mismatching_snps': 6}}) == 'Mismatch'
    assert e.evaluate({'genotyping': {'no_call_chip': 7, 'no_call_seq': 8}}) == 'Unknown'


def test_sex_match():
    e = expressions.SexMatch('called', 'provided')
    assert e.evaluate({'called': 'Male'}) is None
    assert e.evaluate({'called': 'Male', 'provided': 'Male'}) == 'Male'
    assert e.evaluate({'called': 'Male', 'provided': 'Female'}) == 'Mismatch'


def test_matching_species():
    e = expressions.MatchingSpecies('species_contam')
    data = {
        'species_contam': {
            'contaminant_unique_mapped': {'Homo sapiens': 501, 'Thingius thingy': 501, 'Thingius thangy': 500}
        }
    }
    obs = e.evaluate(data)
    assert obs == ['Homo sapiens', 'Thingius thingy']


def test_most_recent():
    e = expressions.MostRecent('procs')
    obs = e.evaluate(
        {
            'procs': [
                {'_created': datetime(2017, 1, 1, 13, 0, 0), 'this': 'that'},
                {'_created': datetime(2017, 1, 1, 13, 30, 0), 'this': 'other'}
            ]
        }
    )
    assert obs['this'] == 'other'


def test_nb_unique_mutable_elements():
    data = [
        {'this': 'other', 'that': 2},
        {'this': 'another', 'that': 1},
        {'this': 'more', 'that': 3}
    ]
    e = expressions.NbUniqueDicts('things', key='this')
    assert e.evaluate({'things': data}) == 3

    e = expressions.NbUniqueDicts('things', key='this', filter_func=lambda x: x['that'] > 1)
    assert e.evaluate({'things': data}) == 2


def test_required_yield():
    e = expressions.RequiredYield('approximate_genome_size')
    assert e.evaluate({'approximate_genome_size': 2100.6}) == {
        '1X': 5,
        '2X': 5,
        '4X': 10,
        '5X': 20,
        '10X': 40,
        '20X': None
    }


def test_yield_for_quoted_coverage():
    e = expressions.RequiredYieldQ30('approximate_genome_size')
    assert e.evaluate({'approximate_genome_size': 2100.6}) == {
        '1X': 4,
        '2X': 4,
        '4X': 8,
        '5X': 16,
        '10X': 32,
        '20X': None
    }
