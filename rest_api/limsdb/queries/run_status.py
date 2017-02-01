from collections import defaultdict
from rest_api.limsdb import queries


class Run:
    def __init__(self):
        self.date_run = None
        self.udfs = {}

    def to_json(self):
        return {
            'date_run': self.date_run,
            'udfs': self.udfs
        }


def run_status(session):
    data = queries.current_runs(session)

    all_runs = defaultdict(Run)
    for date_run, process_id, udf_name, udf_value in data:
        run = all_runs[process_id]
        run.date_run = date_run
        run.udfs[udf_name] = udf_value

    return [r.to_json() for r in all_runs.values()]
