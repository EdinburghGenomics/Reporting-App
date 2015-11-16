__author__ = 'mwham'
import eve
from config import rest_config as cfg

settings = {
    'DOMAIN': {

        'run_elements': {  # for demultiplexing reports, etc
            'url': 'run_elements',
            'item_title': 'element',

            'schema': {
                'run_element_id':       {'type':  'string', 'required':  True, 'unique': True},

                'run_id':               {'type':  'string', 'required':  True},
                'lane':                 {'type': 'integer', 'required':  True},
                'barcode':              {'type':  'string', 'required':  True},
                'project':              {'type':  'string', 'required':  True},

                # for now, treat sample_id and library_id as 1:1 equivalent
                'library_id':           {'type':  'string', 'required':  True},
                'sample_id':            {'type':  'string', 'required':  True},

                'pc_pass_filter':       {'type':   'float', 'required': False},
                'passing_filter_reads': {'type': 'integer', 'required': False},
                'pc_reads_in_lane':     {'type':   'float', 'required': False},
                'yield_in_gb':          {'type':   'float', 'required': False},

                'fastqc_report_r1':     {'type':  'string', 'required': False},
                'fastqc_report_r2':     {'type':  'string', 'required': False},

                'pc_q30_r1':            {'type':   'float', 'required': False},
                'pc_q30_r2':            {'type':   'float', 'required': False}

            }

        },

        'unexpected_barcodes': {
            'url': 'unexpected_barcodes',
            'item_title': 'unexpected_barcode',

            'schema': {
                'run_element_id':       {'type':  'string', 'required':  True, 'unique': True},

                'run_id':               {'type':  'string', 'required':  True},
                'lane':                 {'type': 'integer', 'required':  True},
                'barcode':              {'type':  'string', 'required':  True},
                'passing_filter_reads': {'type':   'float', 'required': False},
                'pc_reads_in_lane':     {'type':   'float', 'required': False}
            }
        },

        'samples': {
            'url': 'samples',

            'schema': {
                'library_id':               {'type':  'string', 'required':  True, 'unique': True},
                'project':                  {'type':  'string', 'required':  True},
                'sample_id':                {'type':  'string', 'required':  True},
                'user_sample_id':           {'type':  'string', 'required': False},

                'yield_in_gb':              {'type':   'float', 'required': False},
                # initial reads used to be 'no adaptor reads'
                'initial_reads':            {'type': 'integer', 'required': False},
                'passing_filter_reads':     {'type': 'integer', 'required': False},
                'nb_mapped_reads':          {'type': 'integer', 'required': False},
                'pc_mapped_reads':          {'type':   'float', 'required': False},
                'nb_properly_mapped_reads': {'type': 'integer', 'required': False},
                'pc_properly_mapped_reads': {'type':   'float', 'required': False},
                'nb_duplicate_reads':       {'type': 'integer', 'required': False},
                'pc_duplicate_reads':       {'type':   'float', 'required': False},
                'median_coverage':          {'type':   'float', 'required': False},
                'pc_callable':              {'type':   'float', 'required': False},

                'pc_q30_r1':                {'type':   'float', 'required': False},
                'pc_q30_r2':                {'type':   'float', 'required': False}
            }
        },

        # 'lanes': {
        #     'schema': {
        #         'run_id': {'type': 'string'},
        #         'lane_number': {},
        #         'pc_pass_filter': {'type': 'number'},
        #         'yield_in_gb'
        #     }
        # }

    },

    'MONGO_HOST': 'localhost',
    'MONGO_PORT': cfg['mongodb_port'],
    'MONGO_DBNAME': 'test_db',
    'ITEMS': 'data',

    'JSONP_ARGUMENT': 'callback',
    'URL_PREFIX': 'api',
    'API_VERSION': '0.1',

    'RESOURCE_METHODS': ['GET', 'POST', 'DELETE'],
    'ITEM_METHODS': ['GET', 'PUT', 'PATCH', 'DELETE']
}

app = eve.Eve(settings=settings)


if __name__ == '__main__':
    """
    querying with Python syntax:
    curl -i -g 'http://host:port/things?where=sample_project=="this"'
    http://host:port/things?where=sample_project==%22this%22

    and MongoDB syntax:
    curl -i -g 'http://host:port/things?where={"sample_project":"this"}'
    http://host:port/things?where={%22sample_project%22:%22this%22}
    """

    if cfg['tornado']:
        import tornado.wsgi
        import tornado.httpserver
        import tornado.ioloop

        http_server = tornado.httpserver.HTTPServer(tornado.wsgi.WSGIContainer(app))
        http_server.listen(cfg['port'])
        tornado.ioloop.IOLoop.instance().start()

    else:
        app.run('localhost', cfg['port'], debug=cfg['debug'])
