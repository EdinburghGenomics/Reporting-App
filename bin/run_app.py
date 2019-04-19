import os
import sys
import argparse
import logging
import logging.config
import logging.handlers
import tornado.wsgi
import tornado.httpserver
import tornado.ioloop
import tornado.autoreload
import signal
from egcg_core.app_logging import LoggingConfiguration
from egcg_core.util import find_files

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

app = None
http_server = None


def run_app(cfg):
    global http_server

    log_cfg = LoggingConfiguration(cfg)
    log_cfg.get_logger('eve', logging.DEBUG)
    log_cfg.get_logger('tornado.access', logging.DEBUG)
    log_cfg.get_logger('tornado.application', logging.DEBUG)
    log_cfg.get_logger('tornado.general', logging.DEBUG)
    log_cfg.configure_handlers_from_config()

    app.logger.info('Started')

    watched_file_patterns = (
        ('etc', '*.yaml'),
        ('reporting_app', 'static', '*.js'),
        ('reporting_app', 'templates', '*.html')
    )
    for pattern in watched_file_patterns:
        for f in find_files(os.path.dirname(__file__), '..', *pattern):
            tornado.autoreload.watch(f)

    tornado.autoreload.watch(cfg.config_file)
    tornado.autoreload.start()

    http_server = tornado.httpserver.HTTPServer(tornado.wsgi.WSGIContainer(app))
    http_server.listen(cfg['port'])
    tornado.ioloop.IOLoop.instance().start()


def stop(sig=None, frame=None):
    if sig or frame:
        app.logger.info('Received signal %s', sig)
    http_server.stop()
    tornado.ioloop.IOLoop.instance().stop()
    app.logger.info('Stopped')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('app', choices=('reporting_app', 'rest_api'))
    args = p.parse_args()

    global app

    if args.app == 'reporting_app':
        import reporting_app
        app = reporting_app.app
        cfg = config.reporting_app_config
    else:
        import rest_api
        app = rest_api.app
        cfg = config.rest_config

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    run_app(cfg)


if __name__ == '__main__':
    main()
