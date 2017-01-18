"""
This script transforms an already-existing database from a v0.10.x (and before) reporting app to the format
required for v0.11. The changes required are:
  - move the data contained in the analysis_driver_proc 'stages' array to its own endpoint called
    'analysis_driver_stages'
  - make analysis_driver_proc.stages a list of IDs, creating a data relation to analysis_driver_stages

This script requires a NoSQL database and an instance of Reporting-App v0.11 to be running.
"""


import argparse
from egcg_core import rest_communication


def transform_proc(proc, comm):
    if 'stages' not in proc:
        return 0

    # split stages off into separate endpoint
    new_stages = []
    for s in proc['stages']:
        s['analysis_driver_proc'] = proc['proc_id']
        s['stage_id'] = '%s_%s' % (proc['proc_id'], s['stage_name'])
        new_stages.append({k: v for k, v in s.items() if not k.startswith('_')})
    comm.post_entry('analysis_driver_stages', new_stages)

    # transform stages array from a list of documents to a list of ids
    new_proc = {k: v for k, v in proc.items() if not k.startswith('_')}
    stages = comm.get_documents(
        'analysis_driver_stages',
        all_pages=True,
        where={'analysis_driver_proc': proc['proc_id']}
    )
    new_proc['stages'] = [s['stage_id'] for s in stages]
    proc_id = new_proc.pop('proc_id')
    comm.patch_entry('analysis_driver_procs', new_proc, 'proc_id', proc_id)


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('--baseurl')
    a.add_argument('--username')
    a.add_argument('--password')
    args = a.parse_args()

    comm = rest_communication.Communicator((args.username, args.password), args.baseurl)

    for doc in comm.get_documents('analysis_driver_procs', all_pages=True):
        transform_proc(doc, comm)
