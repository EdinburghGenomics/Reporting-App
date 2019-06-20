import statistics
from cached_property import cached_property
from egcg_core.app_logging import logging_default
from rest_api import cfg

logger = logging_default.get_logger(__name__)


class Expression:
    def __init__(self, *args, filter_func=None):
        self.args = args
        self.filter_func = filter_func

    def evaluate(self, e):
        raise NotImplementedError


class Calculation(Expression):
    default_return_value = None

    def _expression(self, *args):
        raise NotImplementedError

    def _resolve_element(self, element, query_string):
        e = element.copy()
        queries = query_string.split('.')

        for q in queries[:-1]:
            e = e.get(q, {})
        return e.get(queries[-1])

    def evaluate(self, e):
        if e is None:
            return None

        _args = []
        for a in self.args:
            if isinstance(a, Expression):
                data_point = a.evaluate(e)
            elif isinstance(a, int) or isinstance(a, float):
                # keep the value as they are for numbers
                data_point = a
            elif isinstance(a, str):
                # This is a string describing a query
                data_point = self._resolve_element(e, a)
            else:
                raise ValueError('Unsupported type %s in resolving %s' % (type(a).__name__, type(self).__name__))
            if data_point is None:
                return self.default_return_value

            _args.append(data_point)

        try:
            return self._expression(*_args)
        except (ZeroDivisionError, TypeError) as e:
            logger.error(e)
            return self.default_return_value


class Accumulation(Calculation):
    def _resolve_element(self, element, query_string):  # TODO: make the list nesting level configurable.
        """
        Drill down into the first item of the query string and resolve each item within using the rest of the query
        string.
        """
        e = element.copy()
        queries = query_string.split('.')
        subelements = e.get(queries[0])
        if subelements is None:
            return None

        assert type(subelements) is list, 'In %s: element %s is not a list' % (self.__class__.__name__, element)
        if self.filter_func:
            subelements = list(filter(self.filter_func, subelements))

        resolved_subelements = []
        for s in subelements:
            for q in queries[1:]:
                if q in s:
                    s = s.get(q)
                else:
                    s = None
                    break
            resolved_subelements.append(s)

        return resolved_subelements

    def _expression(self, *args):
        raise NotImplementedError


class Add(Calculation):
    def _expression(self, *args):
        return sum(a for a in args if a is not None)


class Multiply(Calculation):
    def _expression(self, arg1, arg2):
        return arg1 * arg2


class Divide(Calculation):
    def _expression(self, num, denom):
        return num / denom


class Percentage(Divide):
    def _expression(self, num, denom):
        return (num / denom) * 100


class CoefficientOfVariation(Accumulation):
    def _expression(self, elements):
        elements = [e for e in elements if e is not None]
        if len(elements) < 2:
            return 0
        return statistics.stdev(elements) / statistics.mean(elements)


class ToSet(Accumulation):
    default_return_value = []

    def _expression(self, elements):
        return sorted(set(e for e in elements if e is not None))


class Total(Accumulation):
    def _expression(self, elements):
        elements = [e for e in elements if e is not None]
        if not elements:
            return None
        else:
            return sum(elements)


class Reference(Calculation):
    def _expression(self, field):
        return field


class Mean(Accumulation):
    def _expression(self, elements):
        elements = [e for e in elements if e is not None]
        if elements:
            return statistics.mean(elements)


class FirstElement(Accumulation):
    def _expression(self, elements):
        if elements:
            return elements[0]


class StDevPop(Accumulation):
    def _expression(self, elements):
        if elements:
            return statistics.pstdev(elements)


class GenotypeMatch(Calculation):
    def _expression(self, geno_val):
        if not geno_val:
            return None
        elif geno_val['no_call_chip'] + geno_val['no_call_seq'] < 15:
            if geno_val['mismatching_snps'] < 6:
                return 'Match'
            elif geno_val['mismatching_snps'] > 5:
                return 'Mismatch'
        else:
            return 'Unknown'


class SexMatch(Calculation):
    def _expression(self, called, provided):
        if not called or not provided:
            return None
        elif called == provided:
            return called
        else:
            return 'Mismatch'


class MatchingSpecies(Calculation):
    def _expression(self, species_contam):
        return sorted(k for k, v in species_contam['contaminant_unique_mapped'].items() if v > 500)


class RequiredYield(Calculation):
    @cached_property
    def quantised_yields(self):
        return cfg['available_yields']

    def _expression(self, genome_size):
        return {
            # keys have to be strings to be valid BSON
            str(required_coverage) + 'X': self._get_yield(genome_size, required_coverage)
            for required_coverage in cfg['available_coverages']
        }

    def _get_yield(self, genome_size, required_coverage):
        """
        Obtain a required yield, given a particular genome and required X coverage, using the keys of the
        'available_yields' config for candidate yield values.
        :param float genome_size: Genome size in Mb
        :param int required_coverage: X coverage
        :return: required yield in Gb
        """
        exact_yield = genome_size / 1000 * required_coverage
        for y in sorted(self.quantised_yields):
            if y >= exact_yield:
                return y


class RequiredYieldQ30(RequiredYield):
    def _get_yield(self, genome_size, required_coverage):
        """
        Obtain a required yield as per RequiredYield._get_yield, and use the 'available_yields' config to translate it
        into a required yield q30.
        """
        required_yield = super()._get_yield(genome_size, required_coverage)
        if required_yield:
            return self.quantised_yields[required_yield]


class MostRecent(Calculation):
    def __init__(self, *args, date_field='_created'):
        self.date_field = date_field
        super().__init__(*args)

    def _expression(self, elements):
        procs = sorted(elements, key=lambda x: x.get(self.date_field))
        if procs:
            return procs[-1]


class UniqDict(Calculation):
    def __init__(self, *args, filter_func=None, key=None):
        super().__init__(*args, filter_func=filter_func)
        self.key = key

    def _expression(self, elements):
        if self.filter_func:
            elements = [e[self.key] for e in elements if self.filter_func(e)]
        else:
            elements = [e[self.key] for e in elements if e]

        return sorted(set(elements))


class NbUniqueDicts(Calculation):
    def __init__(self, *args, filter_func=None, key=None):
        super().__init__(*args, filter_func=filter_func)
        self.key = key

    def _expression(self, elements):
        if self.filter_func:
            elements = [e[self.key] for e in elements if self.filter_func(e)]
        else:
            elements = [e[self.key] for e in elements if e]

        return len(set(elements))
