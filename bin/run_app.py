import os
import sys
import argparse
import logging
import logging.config
import logging.handlers
import tornado.log
import tornado.wsgi
import tornado.httpserver
import tornado.ioloop
import tornado.autoreload
from egcg_core.app_logging import LoggingConfiguration

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
http_server = None
watched_files = [
    os.path.join(os.path.dirname(__file__), '..', 'etc', 'schema.yaml'),
    os.path.join(os.path.dirname(__file__), '..', 'etc', 'column_mappings.yaml'),
    os.getenv('REPORTINGCONFIG'),
    os.path.expanduser('~/.reporting.yaml')
]


def run_app(app, cfg):
    """
    :param flask.Flask app: A Flask app, or any subclassing object, e.g. eve.Eve
    :param config.Configuration cfg:
    """
    global http_server

    app.debug = cfg.get('debug', False)
    log_cfg = LoggingConfiguration(cfg)

    log_cfg.loggers['tornado.access'] = tornado.log.access_log
    log_cfg.loggers['tornado.app'] = tornado.log.app_log
    log_cfg.loggers['tornado.gen'] = tornado.log.gen_log
    log_cfg.loggers['app'] = app.logger

    app.logger.setLevel(logging.DEBUG)
    log_cfg.configure_handlers_from_config()

    for f in watched_files:
        tornado.autoreload.watch(f)
    tornado.autoreload.start()

    http_server = tornado.httpserver.HTTPServer(tornado.wsgi.WSGIContainer(app))
    http_server.listen(cfg['port'])
    tornado.ioloop.IOLoop.instance().start()


def stop(sig=None, frame=None):
    http_server.stop()
    tornado.ioloop.IOLoop.instance().stop()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('app', choices=['reporting_app', 'rest_api'])
    args = p.parse_args()

    if args.app == 'reporting_app':
        from reporting_app import app
        from config import reporting_app_config as cfg
    else:
        from rest_api import app
        from config import rest_config as cfg

    run_app(app, cfg)


if __name__ == '__main__':
    main()
