
__author__ = 'mwham'
import statistics
import datetime

def resolve(query, element):
    q = {}
    for k, v in query.items():
        q[k] = v.evaluate(element)
    return q


class Expression:
    default_return_value = None

    def __init__(self, *args, filter_func=None):
        self.args = args
        #filter_func is really only valid for accumulations
        self.filter_func = filter_func

    def _expression(self, *args):
        return 0

    def _evaluate(self, *args):
        try:
            return self._expression(*args)
        except (ZeroDivisionError, TypeError):
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
        pparam = param.split('.')
        for e in pparam[:-1]:
            element = element.get(e)
        return element.get(pparam[-1])


class Accumulation(Expression):
    def _resolve_element(self, element, param):
        pparam = param.split('.')
        for p in pparam[:-1]:
            element = element.get(p)
        if element is None:
            return
        if self.filter_func:
            element = list(filter(self.filter_func, element))

        assert type(element) is list, "in %s: element is not a list %s "%(self.__class__.__name__, element)
        return [e.get(pparam[-1]) for e in element]


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

class MostRecent(SingleExp):
    def __init__(self, *args, date_field='_created', date_format='%d_%m_%Y_%H:%M:%S'):
        self.date_field = date_field
        self.date_format = date_format
        super().__init__(*args)

    def _expression(self, elements):
        return sorted(elements, key=lambda x: datetime.datetime.strptime(x.get(self.date_field), self.date_format))[-1]


__all__ = (
    'Constant', 'Add', 'Multiply', 'Divide', 'Percentage', 'CoefficientOfVariation', 'Concatenate',
    'NbUniqueElements', 'Total', 'MostRecent'
)
