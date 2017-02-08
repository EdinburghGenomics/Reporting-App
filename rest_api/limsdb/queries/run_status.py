from collections import defaultdict
from rest_api.limsdb import queries
from flask import request


class Run:
    def __init__(self):
        self.created_date = None
        self.udfs = {}
        self.samples = set()

    def to_json(self):
        return {
            'created_date': self.created_date,
            'run_id': self.udfs['RunID'],
            'run_status': self.udfs['Run Status'],
            'samples': list(self.samples)
        }


def run_status(session):
    data = queries.current_runs(session)
    all_runs = defaultdict(Run)
    for createddate, process_id, udf_name, udf_value, sample_id in data:
        run = all_runs[process_id]
        run.created_date = createddate
        run.udfs[udf_name] = udf_value
        run.samples.add(sample_id)

    status = request.args.get('status', None)
    filterer = lambda r: True
    if status == 'current':
        filterer = lambda r: r.udfs['Run Status'] == 'RunStarted'
    elif status == 'recent':
        filterer = lambda r: r.udfs['Run Status'] != 'RunStarted'

    return sorted((r.to_json() for r in all_runs.values() if filterer(r)), key=lambda r: r['created_date'])
