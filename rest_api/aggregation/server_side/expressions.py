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

    def _evaluate(self, *args):
        return 0

    def _resolve_element(self, e, param):
        pass

    def evaluate(self, e):
        args = []
        if e is None:
            return None
        for a in self.args:
            if isinstance(a, Expression):
                b = a.evaluate(e)
            else:
                b = self._resolve_element(e, a)
            if b is None:
                return self.default_return_value
            args.append(b)
        return self._evaluate(*args)


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
    def _evaluate(self, *args):
        return sum(a for a in args if a is not None)


class Multiply(SingleExp):
    def _evaluate(self, arg1, arg2):
        return arg1 * arg2


class Divide(SingleExp):
    def _evaluate(self, num, denom):
        return num / denom


class Percentage(Divide):
    def _evaluate(self, num, denom):
        return (num / denom) * 100


class CoefficientOfVariation(Accumulation):
    def _evaluate(self, elements):
        elements = [e for e in elements if e is not None]
        if len(elements) < 2:
            return 0
        return statistics.stdev(elements) / statistics.mean(elements)


class Concatenate(Accumulation):
    default_return_value = ''

    def _evaluate(self, elements):
        return list(sorted(set(elements)))


class NbUniqueElements(SingleExp):
    def _evaluate(self, elements):
        elements = [e for e in elements if e is not None]
        return len(set(elements))

class Total(Accumulation):
    def _evaluate(self, elements):
        elements = [e for e in elements if e is not None]
        if not elements:
            return None
        else:
            return sum(elements)
