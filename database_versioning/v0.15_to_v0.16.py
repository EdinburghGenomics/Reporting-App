
import argparse

import datetime
import pymongo
import sys, os

from egcg_core import clarity
from egcg_core.app_logging import logging_default as log_cfg
from egcg_core.exceptions import ConfigError
from egcg_core.rest_communication import Communicator

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import rest_config as rest_cfg
from config import reporting_app_config as app_cfg

from bin.retrigger_aggregation import retrigger_aggregation_run_element


if __name__ == '__main__':

    log_cfg.add_stdout_handler()
    app_logger = log_cfg.get_logger('migration_v0.15_v0.16')

    a = argparse.ArgumentParser()
    a.add_argument('--username', required=True)
    a.add_argument('--password', required=True)
    args = a.parse_args()

    # check the config is set
    if not rest_cfg or not app_cfg or 'db_host' not in rest_cfg or 'rest_api' not in app_cfg:
        raise ConfigError('Configuration file was not set or is missing values')


    cli = pymongo.MongoClient(rest_cfg['db_host'], rest_cfg['db_port'])
    db = cli[rest_cfg['db_name']]

    # Rename the variable in the mongo database
    collection = db['samples']
    collection.update_many({}, {'$rename': {"expected_yield": "required_yield_q30"}})
    collection.update_many({}, {'$rename': {"expected_coverage": "required_coverage"}})

    # upload the recent samples using data from the LIMS
    year_ago = datetime.datetime.now() - datetime.timedelta(days=365)
    clarity.connection(**rest_cfg.get('clarity'))
    samples = list(collection.find({"_created": {'$gt': year_ago}}))
    app_logger.info('Update %s samples' % len(samples))
    app_logger.info('Query the lims for %s samples' % len(samples))
    sample_names = [sample.get('sample_id') for sample in samples]
    clarity.get_list_of_samples(sample_names)
    app_logger.info('Update %s samples in database', len(sample_names))
    counter = 0
    for element in samples:
        sample_id = element['sample_id']
        lims_sample = clarity.get_samples(sample_id)

        if lims_sample:
            lims_sample = lims_sample[0]
            payload = {}
            if 'Required Yield (Gb)' in lims_sample.udf:
                payload['required_yield'] = lims_sample.udf['Required Yield (Gb)'] * 1000000000

            if 'Yield for Quoted Coverage (Gb)' in lims_sample.udf:
                payload['required_yield_q30'] = lims_sample.udf['Yield for Quoted Coverage (Gb)'] * 1000000000

            if 'Coverage (X)' in lims_sample.udf:
                payload['required_coverage'] = lims_sample.udf['Coverage (X)']

            collection.update_one({'sample_id': sample_id}, {'$set': payload})
        counter += 1
        if counter % 100 == 0:
            app_logger.info('%s samples updated' % counter)

    app_logger.info('%s samples updated' % counter)
    app_logger.info("Retrigger aggregation")
    retrigger_aggregation_run_element(Communicator(auth=(args.username, args.password), baseurl=app_cfg['rest_api']))


