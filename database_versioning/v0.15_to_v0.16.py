
import argparse

import datetime
import pymongo
import sys, os

from egcg_core import clarity

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import rest_config as cfg


if __name__ == '__main__':
    a = argparse.ArgumentParser()
    args = a.parse_args()

    cli = pymongo.MongoClient(cfg['db_host'], cfg['db_port'])
    db = cli[cfg['db_name']]

    # Rename the variable in the mongo database
    collection = db['samples']
    collection.update_many({}, {'$rename': {"expected_yield": "required_yield_q30"}})
    collection.update_many({}, {'$rename': {"expected_coverage": "required_coverage"}})

    # upload the recent samples using data from the LIMS
    year_ago = datetime.datetime.now() - datetime.timedelta(days=365)
    clarity.connection(**cfg.get('clarity'))
    samples = list(collection.find({"_created": {'$gt': year_ago}}))
    print('Update %s samples' % len(samples))
    print('Query the lims for %s samples' % len(samples))
    sample_names = [sample.get('sample_id') for sample in samples]
    clarity.get_list_of_samples(sample_names)
    print('Update database')
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
            print('%s samples updated' % counter)



