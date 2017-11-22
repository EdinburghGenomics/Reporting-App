import argparse
from egcg_core.rest_communication import Communicator
from egcg_core.app_logging import logging_default

"""
This script runs through all run elements and patches each with a null entity, retriggering database hook aggregation.
Superelements will be re-aggregated automatically.
"""


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--baseurl', required=True)
    a.add_argument('--username', required=True)
    a.add_argument('--password', required=True)
    args = a.parse_args()

    logging_default.add_stdout_handler()
    c = Communicator((args.username, args.password), args.baseurl)
    retrigger_aggregation(c)


def retrigger_aggregation(communicator):
    all_runs = communicator.get_documents('runs', all_pages=True)
    for r in all_runs:
        communicator.patch_entries('run_elements', {}, where={'run_id': r['run_id']})


if __name__ == '__main__':
    main()
