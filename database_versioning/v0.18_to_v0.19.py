import os
import sys
import argparse
from egcg_core.app_logging import logging_default as log_cfg
from egcg_core.exceptions import ConfigError
from egcg_core.rest_communication import Communicator

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import reporting_app_config as app_cfg
from bin.retrigger_aggregation import retrigger_aggregation_samples

if __name__ == '__main__':

    log_cfg.add_stdout_handler()
    app_logger = log_cfg.get_logger('migration_v0.18_v0.19')

    a = argparse.ArgumentParser()
    a.add_argument('--username', required=True)
    a.add_argument('--password', required=True)
    args = a.parse_args()

    # check the config is set
    if not app_cfg or 'rest_api' not in app_cfg:
        raise ConfigError('Configuration file was not set or is missing values')

    app_logger.info('Retrigger aggregation')
    c = Communicator(auth=(args.username, args.password), baseurl=app_cfg['rest_api'])
    retrigger_aggregation_samples(c)


