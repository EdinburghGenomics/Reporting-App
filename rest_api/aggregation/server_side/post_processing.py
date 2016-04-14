
class PostProcessor:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def func(self, *args, **kwargs):
        raise NotImplementedError

    def __call__(self, agg):
        return self.func(agg, *self.args, **self.kwargs)


class select_column(PostProcessor):
    def func(self, agg, column):
        return sorted([e[column] for e in agg])


class cast_to_sets(PostProcessor):
    def func(self, agg, *columns):
        for e in agg:
            for c in columns:
                e[c] = set(e[c])
        return agg


class date_to_string(PostProcessor):
    def func(self, agg, *columns):
        for e in agg:
            for c in columns:
                e[c] = str(e[c])
        return agg
