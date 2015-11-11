__author__ = 'mwham'
import argparse
import eve

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('-p', '--port', type=int, help='port to run Eve API on')
    p.add_argument('-d', '--debug', action='store_true', help='run the app in debug mode')
    p.add_argument('-m', '--mongodb-port', type=int, help='port that mongoDB server is running on')
    p.add_argument(
        '-t',
        '--tornado',
        action='store_true',
        help='whether to use Tornado\'s http server and wsgi container for external access'
    )
    args = p.parse_args()

    settings = {
        'DOMAIN': {

            'run_elements': {  # for demultiplexing reports, etc
                'url': 'run_elements',
                'item_title': 'element',
                'id_field': 'id',

                'schema': {
                    'id':                   {'type': 'string', 'required': True, 'unique': True},

                    'run_id':               {'type':  'string', 'required': True},
                    'lane':                 {'type': 'integer', 'required': True},
                    'barcode':              {'type':  'string', 'required': True},
                    'project':              {'type':  'string', 'required': True},

                    # for now, treat sample_id and library_id as 1:1 equivalent
                    'library_id':           {'type':  'string', 'required': True},
                    'sample_id':            {'type':  'string', 'required': True},

                    'pc_pass_filter':       {'type':   'float', 'required': True},
                    'passing_filter_reads': {'type': 'integer', 'required': True},
                    'pc_reads_in_lane':     {'type':   'float', 'required': True},
                    'yield_in_gb':          {'type':   'float', 'required': True},

                    'pc_q30_r1':            {'type':   'float', 'required': True},
                    'pc_q30_r2':            {'type':   'float', 'required': True}

                }

            },

            'unexpected_barcodes': {
                'url': 'unexpected_barcodes',
                'item_title': 'unexpected_barcode',
                'id_field': 'id',

                'schema': {
                    'id':                   {'type': 'string', 'required': True, 'unique': True},

                    'run_id':               {'type':  'string', 'required': True},
                    'lane':                 {'type': 'integer', 'required': True},
                    'barcode':              {'type':  'string', 'required': True},
                    'passing_filter_reads': {'type':   'float', 'required': True},
                    'pc_reads_in_lane':     {'type':   'float', 'required': True}
                }
            },

            'samples': {
                'url': 'samples',
                'id_field': 'library_id',

                'schema': {
                    'project':                  {'type': 'string', 'required': True},
                    'library_id':               {'type': 'string', 'required': True, 'unique': True},
                    'sample_id':                {'type': 'string', 'required': True},
                    'user_sample_id':           {'type': 'string', 'required': True},

                    'yield_in_gb':              {'type':   'float', 'required': True},
                    'initial_reads':            {'type': 'integer', 'required': True},  # used to be 'no adaptor reads'
                    'passing_filter_reads':     {'type': 'integer', 'required': True},
                    'nb_mapped_reads':          {'type': 'integer', 'required': True},
                    'pc_mapped_reads':          {'type':   'float', 'required': True},
                    'nb_properly_mapped_reads': {'type': 'integer', 'required': True},
                    'pc_properly_mapped_reads': {'type':   'float', 'required': True},
                    'nb_duplicate_reads':       {'type': 'integer', 'required': True},
                    'pc_duplicate_reads':       {'type':   'float', 'required': True},
                    'median_coverage':          {'type':   'float', 'required': True},
                    'pc_callable':              {'type':   'float', 'required': True},
                    'pc_q30_r1':                {'type':   'float', 'required': True},
                    'pc_q30_r2':                {'type':   'float', 'required': True}
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

    app = eve.Eve(settings=settings)

    """
    querying with Python syntax:
    curl -i -g 'http://host:port/things?where=sample_project=="this"'
    http://host:port/things?where=sample_project==%22this%22

    and MongoDB syntax:
    curl -i -g 'http://host:port/things?where={"sample_project":"this"}'
    http://host:port/things?where={%22sample_project%22:%22this%22}
    """

    if args.tornado:
        import tornado.wsgi
        import tornado.httpserver
        import tornado.ioloop

        http_server = tornado.httpserver.HTTPServer(tornado.wsgi.WSGIContainer(app))
        http_server.listen(args.port)
        tornado.ioloop.IOLoop.instance().start()

    else:
        app.run('localhost', 4999, debug=args.debug)
