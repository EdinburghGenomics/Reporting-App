from collections import defaultdict
from rest_api.limsdb import queries
from flask import request
from datetime import datetime, timedelta



class Run:
    def __init__(self):
        self.created_date = None
        self.udfs = {}
        self.samples = set()
        self.projects = set()

    def to_json(self):
        return {
            'created_date': self.created_date,
            'run_id': self.udfs['RunID'],
            'run_status': self.udfs['Run Status'],
            'samples': sorted(list(self.samples)),
            'project_ids': sorted(list(self.projects))
        }


def run_status(session):
    # TODO: make the time threshold a parameter
    now = datetime.now()
    threshold = now - timedelta(7)
    data = queries.runs_info(session, time_since = threshold)
    all_runs = defaultdict(Run)

    for createddate, process_id, udf_name, udf_value, lane, sample_id, project_id in data:
        run = all_runs[process_id]
        run.created_date = createddate
        run.udfs[udf_name] = udf_value
        run.samples.add(sample_id)
        run.projects.add(project_id)

    status = request.args.get('status', None)
    filterer = lambda r: True
    if status == 'current':
        filterer = lambda r: r.udfs['Run Status'] == 'RunStarted'
    elif status == 'recent':
        filterer = lambda r: r.udfs['Run Status'] != 'RunStarted'

    return sorted((r.to_json() for r in all_runs.values() if filterer(r)), key=lambda r: r['created_date'])
