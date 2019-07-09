import os
import sys
import pymongo
import argparse
from egcg_core.app_logging import logging_default as log_cfg
from egcg_core.rest_communication import Communicator

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import rest_config as rest_cfg


if __name__ == '__main__':
    log_cfg.add_stdout_handler()
    app_logger = log_cfg.get_logger('migration_v0.21_v0.22')

    a = argparse.ArgumentParser()
    a.add_argument('baseurl')
    a.add_argument('username')
    a.add_argument('password')
    args = a.parse_args()

    c = Communicator(auth=(args.username, args.password), baseurl=args.baseurl)
    cli = pymongo.MongoClient(rest_cfg['db_host'], rest_cfg['db_port'])
    db = cli[rest_cfg['db_name']]
    collection = db['samples']

    query = {'gender_validation': {'$exists': True}}
    app_logger.info('Renaming gender to sex for %s samples', collection.count(query))
    count = 0
    for s in collection.find(query):
        count += 1
        if count % 100 == 0:
            app_logger.info('%s samples processed', count)

        called = s.get('called_gender')
        provided = s.get('provided_gender')
        validation = s['gender_validation']

        if called:
            validation['called'] = called

        if provided:
            validation['provided'] = provided

        collection.update(
            {'sample_id': s['sample_id']},
            {
                '$set': {'sex_validation': validation},
                '$unset': {
                    'called_gender': None,
                    'provided_gender': None,
                    'gender_validation': None
                }
            }
        )

    app_logger.info('Retriggering aggregation for all %s samples', collection.count())
    c.patch_entries('samples', {}, all_pages=True)
