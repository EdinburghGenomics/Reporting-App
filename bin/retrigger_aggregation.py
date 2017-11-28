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
    retrigger_aggregation(c)


def retrigger_aggregation(communicator, **filter):
    all_runs = communicator.get_documents('runs', all_pages=True, **filter)
    app_logger.info('%s runs to process', len(all_runs))
    count = 0
    for r in all_runs:
        count += 1
        if count % 100 == 0:
            app_logger.info('%s runs processed', count)
        communicator.patch_entries('run_elements', {}, where={'run_id': r['run_id']})


if __name__ == '__main__':
    main()
