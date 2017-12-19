import statistics
import datetime
from egcg_core.app_logging import logging_default

logger = logging_default.get_logger(__name__)


def resolve(query, element):
    q = {}
    for k, v in query.items():
        if isinstance(v, Expression):
            q[k] = v.evaluate(element)
        elif isinstance(v, dict):
            # recurse for dictionaries
            q[k] = resolve(v, element)
        else:
            raise ValueError('Unsupported type %s for key %s' % (type(v), k))
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


__all__ = (
    'resolve', 'Calculation', 'Accumulation', 'Add', 'Multiply', 'Divide', 'Percentage',
    'CoefficientOfVariation', 'ToSet', 'NbUniqueElements', 'Total', 'MostRecent'
)
