__author__ = 'mwham'
import argparse
import eve

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-p', '--port', type=int, help='port to run Eve API on')
    p.add_argument('-m', '--mongodb-port', type=int, help='port that mongoDB server is running on')
    args = p.parse_args()

    settings = {
        'DOMAIN': {

            'run_elements': {  # for demultiplexing reports, etc
                'url': 'run_elements',
                'resource_methods': ['GET', 'POST', 'DELETE'],
                'item_title': 'element',

                'schema': {
                    'run_id':               {'type':  'string'},
                    'lane':                 {'type': 'integer'},
                    'barcode':              {'type':  'string'},
                    'project':              {'type':  'string'},

                    # for now, treat sample_id and library_id as 1:1 equivalent
                    'library_id':           {'type':  'string'},
                    'sample_id':            {'type':  'string'},

                    'pc_pass_filter':       {'type':   'float'},
                    'passing_filter_reads': {'type': 'integer'},
                    'yield_in_gb':          {'type':   'float'},

                    'pc_q30_r1':            {'type':   'float'},
                    'pc_q30_r2':            {'type':   'float'}

                }

            },

            'unexpected_barcodes': {
                'url': 'unexpected_barcodes',

                'schema': {
                    'run_id':               {'type':  'string'},
                    'lane':                 {'type': 'integer'},
                    'barcode':              {'type':  'string'},
                    'passing_filter_reads': {'type':   'float'},
                    'pc_reads_in_lane':     {'type':   'float'}
                }
            },

            'samples': {
                'url': 'samples',

                'schema': {
                    'project':                  {'type': 'string'},
                    'library_id':               {'type': 'string'},
                    'sample_id':                {'type': 'string'},
                    'user_sample_id':           {'type': 'string'},

                    'yield_in_gb':              {'type':   'float'},
                    'initial_reads':            {'type': 'integer'},  # used to be 'no adaptor reads'
                    'passing_filter_reads':     {'type': 'integer'},
                    'nb_mapped_reads':          {'type': 'integer'},
                    'pc_mapped_reads':          {'type':   'float'},
                    'nb_properly_mapped_reads': {'type': 'integer'},
                    'pc_properly_mapped_reads': {'type':   'float'},
                    'nb_duplicate_reads':       {'type': 'integer'},
                    'pc_duplicate_reads':       {'type':   'float'},
                    'median_coverage':          {'type':   'float'},
                    'pc_callable':              {'type':   'float'},
                    'pc_q30_r1':                {'type':   'float'},
                    'pc_q30_r2':                {'type':   'float'}
                }
            },

            # 'lanes': {
            #     'schema': {
            #         'run_id': {
            #             'type': 'string'
            #         },
            #         'lane_number': {
            #
            #         },
            #
            #         'pc_pass_filter': {
            #             'type': 'number',
            #
            #         }
            #     }
            # }

        },

        'MONGO_HOST': 'localhost',
        'MONGO_PORT': args.mongodb_port,
        'MONGO_DBNAME': 'test_db',
        'ITEMS': 'data',

        'JSONP_ARGUMENT': 'callback',
        'URL_PREFIX': 'api',
        'API_VERSION': '0.1',

        'RESOURCE_METHODS': ['GET', 'POST', 'DELETE'],
        'ITEM_METHODS': ['GET', 'PUT', 'DELETE']
    }

    for k, v in settings['DOMAIN'].items():
        schema = v.get('schema')
        if schema:
            for field, config in schema.items():
                config['required'] = True

    app = eve.Eve(settings=settings)

    """
    querying with Python syntax:
    curl -i -g 'http://host:port/things?where=sample_project=="this"'
    http://host:port/things?where=sample_project==%22this%22

    and MongoDB syntax:
    curl -i -g 'http://host:port/things?where={"sample_project":"this"}'
    http://host:port/things?where={%22sample_project%22:%22this%22}
    """

    args = p.parse_args()
    app.run(port=args.port, debug=True)
