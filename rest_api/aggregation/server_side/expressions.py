__author__ = 'mwham'
import statistics


def resolve(query, element, embedded_field=None):
    q = {}
    for k, v in query.items():
        if isinstance(v, SingleExp):
            q[k] = v.evaluate(element)
        elif isinstance(v, Accumulation):
            q[k] = v.evaluate(element.get(embedded_field))
    return q


class Expression:
    default_return_value = 0

    def __init__(self, *args):
        self.args = args

    def _expression(self, *args):
        return 0

    def _evaluate(self, *args):
        try:
            return self._expression(*args)
        except (ZeroDivisionError,):
            return self.default_return_value

    def _resolve_element(self, e, param):
        pass

    def evaluate(self, e):
        data = []
        if e is None:
            return None
        for a in self.args:
            if isinstance(a, Expression):
                data_point = a.evaluate(e)
            else:
                data_point = self._resolve_element(e, a)
            if data_point is None:
                return self.default_return_value
            data.append(data_point)
        return self._evaluate(*data)


class SingleExp(Expression):
    def _resolve_element(self, element, param):
        return element.get(param)


class Accumulation(Expression):
    def _resolve_element(self, elements, param):
        return [e.get(param) for e in elements]


class Constant(Expression):
    def evaluate(self, e):
        return self.args[0]


class Add(SingleExp):
    def _expression(self, *args):
        return sum(a for a in args if a is not None)


class Multiply(SingleExp):
    def _expression(self, arg1, arg2):
        return arg1 * arg2


class Divide(SingleExp):
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


class NbUniqueElements(SingleExp):
    def _expression(self, elements):
        elements = [e for e in elements if e is not None]
        return len(set(elements))


class Total(Accumulation):
    def _expression(self, elements):
        elements = [e for e in elements if e is not None]
        if not elements:
            return None
        else:
            return sum(elements)

__all__ = (
    'Constant', 'Add', 'Multiply', 'Divide', 'Percentage', 'CoefficientOfVariation', 'Concatenate',
    'NbUniqueElements', 'Total'
)
