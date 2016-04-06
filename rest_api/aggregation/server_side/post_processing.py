from ..database_side import queries


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


class most_recent_proc(PostProcessor):
    def func(self, agg, db, dataset_name):
        for e in agg:
            cursor = db['analysis_driver_procs'].aggregate(queries.most_recent_proc(dataset_name))
            procs = list(cursor)
            assert len(procs) == 1

            e['most_recent_proc'] = procs[0]
        return agg
