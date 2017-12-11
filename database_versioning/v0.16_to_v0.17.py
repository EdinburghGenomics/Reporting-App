
import argparse

import datetime
import sys, os

from egcg_core.app_logging import logging_default as log_cfg
from egcg_core.exceptions import ConfigError
from egcg_core.rest_communication import Communicator
from pymongo import settings

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import reporting_app_config as app_cfg

from bin.retrigger_aggregation import retrigger_aggregation


if __name__ == '__main__':

    log_cfg.add_stdout_handler()
    app_logger = log_cfg.get_logger('migration_v0.16_v0.17')

    a = argparse.ArgumentParser()
    a.add_argument('--username', required=True)
    a.add_argument('--password', required=True)
    args = a.parse_args()

    # check the config is set
    if not app_cfg or 'rest_api' not in app_cfg:
        raise ConfigError('Configuration file was not set or is missing values')

    two_month_ago = datetime.datetime.now() - datetime.timedelta(days=60)

    app_logger.info("Retrigger aggregation")
    # only retrigger aggregation on recent runs
    retrigger_aggregation(
        Communicator(auth=(args.username, args.password), baseurl=app_cfg['rest_api']),
        where={'_created': {'$gte': two_month_ago.strftime(settings.DATE_FORMAT)}}
    )


