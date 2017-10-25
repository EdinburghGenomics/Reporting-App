import statistics


def resolve(query, element):
    q = {}
    for k, v in query.items():
        q[k] = v.evaluate(element)
    return q


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
            else:
                data_point = self._resolve_element(e, a)

            if data_point is None:
                return self.default_return_value

            _args.append(data_point)

        try:
            return self._expression(*_args)
        except (ZeroDivisionError, TypeError):
            return self.default_return_value


class Accumulation(Calculation):
    def _resolve_element(self, element, query_string):
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
                s = s.get(q)
            resolved_subelements.append(s)

        return resolved_subelements

    def _expression(self, *args):
        raise NotImplementedError


class Constant(Expression):
    def evaluate(self, e):
        return self.args[0]


class Reference(Calculation):
    def _expression(self, field):
        return field


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


class Concatenate(Accumulation):
    default_return_value = ''

    def _expression(self, elements):
        return list(sorted(set(elements)))


class NbUniqueElements(Calculation):
    def _expression(self, elements):
        elements = [e for e in elements if e is not None]
        if self.filter_func:
            elements = [e for e in elements if self.filter_func(e)]

        return len(elements)


class Total(Accumulation):
    def _expression(self, elements):
        elements = [e for e in elements if e is not None]
        if not elements:
            return None
        else:
            return sum(elements)


class Mean(Accumulation):
    def _expression(self, elements):
        if elements:
            return sum(elements) / len(elements)


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


class SexCheck(Calculation):
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


class MostRecent(Calculation):
    def __init__(self, *args, date_field='_created', date_format='%d_%m_%Y_%H:%M:%S'):
        self.date_field = date_field
        self.date_format = date_format
        super().__init__(*args)

    def _expression(self, elements):
        procs = sorted(
            elements,
            key=lambda x: x.get(self.date_field)
        )
        if procs:
            return procs[-1]


__all__ = (
    'Constant', 'Add', 'Multiply', 'Divide', 'Percentage', 'CoefficientOfVariation', 'Concatenate',
    'NbUniqueElements', 'Total', 'MostRecent', 'Mean', 'FirstElement', 'StDevPop', 'GenotypeMatch', 'SexCheck',
    'MatchingSpecies', 'Reference', 'resolve'
)
