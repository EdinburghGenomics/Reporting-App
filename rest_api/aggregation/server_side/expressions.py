import statistics
import datetime


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
        if self.filter_func:
            elements = [e for e in elements if self.filter_func(e)]
        else:
            elements = [e for e in elements if e is not None]

        return len(set(elements))


class Total(Accumulation):
    def _expression(self, elements):
        elements = [e for e in elements if e is not None]
        if not elements:
            return None
        else:
            return sum(elements)


class MostRecent(Calculation):
    def __init__(self, *args, date_field='_created', date_format='%d_%m_%Y_%H:%M:%S'):
        self.date_field = date_field
        self.date_format = date_format
        super().__init__(*args)

    def _expression(self, elements):
        return sorted(elements,
                      key=lambda x: datetime.datetime.strptime(x.get(self.date_field), self.date_format))[-1]
