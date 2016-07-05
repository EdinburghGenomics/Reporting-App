import os
import argparse
import logging
import logging.config
import logging.handlers
import egcg_core.config
from egcg_core.app_logging import logging_default as log_cfg

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
    webserver = cfg.get('webserver', 'werkzeug')
    app.debug = cfg.get('debug', False)

    egcg_core.config.cfg.load_config_file(os.getenv('REPORTINGCONFIG'))
    log_cfg.loggers.update(_webserver_loggers(webserver))
    log_cfg.loggers['app'] = app.logger
    app.logger.setLevel(logging.DEBUG)
    log_cfg.configure_handlers_from_config()

    if webserver == 'tornado':
        run_tornado(app, cfg)
    else:
        run_werkzeug(app, cfg)


def run_tornado(app, cfg):
    import tornado.wsgi
    import tornado.httpserver
    import tornado.ioloop
    import tornado.autoreload

    for f in watched_files:
        tornado.autoreload.watch(f)
    tornado.autoreload.start()

    http_server = tornado.httpserver.HTTPServer(tornado.wsgi.WSGIContainer(app))
    http_server.listen(cfg['port'])
    tornado.ioloop.IOLoop.instance().start()


def run_werkzeug(app, cfg):
    import werkzeug.serving
    werkzeug.serving.run_simple(
        'localhost',
        cfg['port'],
        app,
        use_reloader=True,
        extra_files=watched_files
    )


def _webserver_loggers(webserver):
    if webserver == 'werkzeug':
        import werkzeug._internal
        # werkzeug's default logger is None until werkzeug._default._log is called. Initialise it to a
        # logging.Logger here, and set it
        werkzeug._internal._logger = logging.getLogger('werkzeug')
        werkzeug._internal._logger.setLevel(logging.DEBUG)
        return {'werkzeug': werkzeug._internal._logger}

    elif webserver == 'tornado':
        import tornado.log
        return {'tornado.access': tornado.log.access_log, 'tornado.app': tornado.log.app_log, 'tornado.gen': tornado.log.gen_log}

    else:
        raise AssertionError("webserver %s should be one of 'werkzeug' or 'tornado'" % webserver)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('app', choices=['reporting_app', 'rest_api'])
    args = p.parse_args()

    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    if args.app == 'reporting_app':
        from reporting_app import app
        from config import reporting_app_config as cfg
    else:
        from rest_api import app
        from config import rest_config as cfg

    run_app(app, cfg)


if __name__ == '__main__':
    main()
