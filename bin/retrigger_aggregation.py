import argparse
from egcg_core.rest_communication import Communicator
from egcg_core.app_logging import logging_default as log_cfg

"""
This script runs through all run elements and patches each with a null entity, retriggering database hook aggregation.
Superelements will be re-aggregated automatically.
"""

app_logger = log_cfg.get_logger('retrigger_aggregation')


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--baseurl', required=True)
    a.add_argument('--username', required=True)
    a.add_argument('--password', required=True)
    args = a.parse_args()

    log_cfg.add_stdout_handler()
    c = Communicator((args.username, args.password), args.baseurl)
    retrigger_aggregation_run_elements(c)


def retrigger_aggregation_run_elements(communicator, **params):
    all_runs = communicator.get_documents('runs', all_pages=True, **params)
    app_logger.info('%s runs to process', len(all_runs))
    count = 0
    for r in all_runs:
        count += 1
        if count % 100 == 0:
            app_logger.info('%s runs processed', count)
        communicator.patch_entries('run_elements', {}, where={'run_id': r['run_id']})


def retrigger_aggregation_lanes(communicator, **params):
    all_runs = communicator.get_documents('runs', all_pages=True, **params)
    app_logger.info('%s runs to process', len(all_runs))
    count = 0
    for r in all_runs:
        count += 1
        if count % 100 == 0:
            app_logger.info('%s runs processed', count)
        communicator.patch_entries('lanes', {}, where={'run_id': r['run_id']})


def retrigger_aggregation_projects(communicator, **params):
    all_projects = communicator.get_documents('projects', all_pages=True, **params)
    app_logger.info('%s project to process', len(all_projects))
    count = 0
    for p in all_projects:
        count += 1
        if count % 100 == 0:
            app_logger.info('%s projects processed', count)
        communicator.patch_entry('projects', {}, 'project_id', p['project_id'])


def retrigger_aggregation_samples(communicator, **params):
    all_samples= communicator.get_documents('samples', all_pages=True, **params)
    app_logger.info('%s samples to process', len(all_samples))
    count = 0
    for s in all_samples:
        count += 1
        if count % 100 == 0:
            app_logger.info('%s samples processed', count)
        communicator.patch_entry('samples', {}, 'sample_id', s['sample_id'])


if __name__ == '__main__':
    main()
