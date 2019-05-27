import argparse
from egcg_core.app_logging import logging_default as log_cfg
from egcg_core.rest_communication import Communicator


if __name__ == '__main__':
    log_cfg.add_stdout_handler()
    app_logger = log_cfg.get_logger('migration_v0.21_v0.22')

    a = argparse.ArgumentParser()
    a.add_argument('baseurl')
    a.add_argument('username')
    a.add_argument('password')
    args = a.parse_args()

    app_logger.info('Retrigger aggregation')
    c = Communicator(auth=(args.username, args.password), baseurl=args.baseurl)
    samples = c.get_documents(
        'samples',
        where={'aggregated.from_all_run_elements': {'$exists': False}},
        all_pages=True
    )

    app_logger.info('Reaggregating %s samples', len(samples))
    count = 0
    for s in samples:
        count += 1
        if count % 100 == 0:
            app_logger.info('%s samples processed', count)

        c.patch_entry('samples', {}, 'sample_id', s['sample_id'])
