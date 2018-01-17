from collections import defaultdict

from rest_api.common import retrieve_args
from rest_api.limsdb import queries
from rest_api.limsdb.queries import format_date


class Run:
    def __init__(self):
        self.created_date = None
        self.cst_date = None
        self.udfs = {}
        self.samples = set()
        self.projects = set()

    def to_json(self):
        return {
            'created_date': format_date(self.created_date),
            'cst_date': format_date(self.cst_date),
            'run_id': self.udfs['RunID'],
            'run_status': self.udfs['Run Status'],
            'sample_ids': sorted(list(self.samples)),
            'project_ids': sorted(list(self.projects)),
            'instrument_id': self.udfs['InstrumentID'],
            'nb_reads': self.udfs['Read'],
            'nb_cycles': self.udfs['Cycle']
        }


def run_status(session):
    kwargs = retrieve_args()
    time_since = kwargs.get('createddate', None)
    status = kwargs.get('status', None)
    all_runs = defaultdict(Run)

    for data in queries.runs_info(session, time_since=time_since):
        createddate, process_id, udf_name, udf_value, lane, sample_id, project_id = data
        run = all_runs[process_id]
        run.created_date = createddate
        run.udfs[udf_name] = udf_value
        run.samples.add(sample_id)
        run.projects.add(project_id)
    for data in queries.runs_cst(session, time_since=time_since):
        process_id, cst_process_id, cst_date = data
        run = all_runs[process_id]
        run.cst_date = cst_date

    filterer = lambda r: True
    if status == 'current':
        filterer = lambda r: r.udfs['Run Status'] == 'RunStarted'
    elif status == 'recent':
        filterer = lambda r: r.udfs['Run Status'] != 'RunStarted'

    return sorted((r.to_json() for r in all_runs.values() if filterer(r)), key=lambda r: r['created_date'])
