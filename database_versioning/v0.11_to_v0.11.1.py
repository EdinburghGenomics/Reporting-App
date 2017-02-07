"""
This script transforms an already-existing database from a v0.11 reporting app to the format
required for v0.11.1 The changes required are:
  - Move deletion information contained in the analysis_driver_proc.status to sample.data_deleted
    analysis_driver_proc.status = deleted  ==> sample.data_deleted = all
  - reverting analysis_driver_proc.status = finished

This script requires a NoSQL database and an instance of Reporting-App v0.11.1 to be running.
"""


import argparse
from egcg_core import rest_communication


def find_deleted_samples(comm):
    return comm.get_documents(
        'aggregate/samples',
        quiet=True,
        match={'proc_status': 'deleted'},
        paginate=False
    )


def update_data_deleted(comm, samples):
    for sample in samples:
        comm.patch_entry(
            'samples',
            {'data_deleted': 'all'},
            'sample_id', sample.get('sample_id')
        )


def update_most_recent_proc(comm, samples):
    for sample in samples:
        patch_content = sample.get('most_recent_proc')
        patch_content['status'] = 'finished'
        element_id = patch_content.pop('proc_id')
        comm.patch_entry(
            'analysis_driver_procs',
            patch_content,
            id_field='proc_id',
            element_id=element_id
        )


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    a.add_argument('--baseurl')
    a.add_argument('--username')
    a.add_argument('--password')
    args = a.parse_args()

    comm = rest_communication.Communicator((args.username, args.password), args.baseurl)

    samples = find_deleted_samples(comm)
    update_data_deleted(comm, samples)
    update_most_recent_proc(comm, samples)
