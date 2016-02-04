__author__ = 'mwham'
import sys
import os
import multiprocessing
import logging
import logging.config
import logging.handlers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import reporting_app
import rest_api
from config import rest_config, reporting_app_config

watched_files = [
    os.path.join(os.path.dirname(__file__), '..', 'etc', 'example_reporting.yaml')
]



def run_app(app, cfg):
    """
    :param Flask app: A Flask app, or any subclassing object, e.g. eve.Eve
    :param config.Configuration cfg:
    """
    webserver = cfg.get('webserver', 'werkzeug')
    _configure_logging(app.logger, cfg.get('logging', {}), webserver)
    app.logger.info('Starting with configuration: ' + str(cfg.content))

    app.debug = cfg.get('debug', False)

    if webserver == 'tornado':
        import tornado.wsgi
        import tornado.httpserver
        import tornado.ioloop

        http_server = tornado.httpserver.HTTPServer(tornado.wsgi.WSGIContainer(app))
        http_server.listen(cfg['port'])
        tornado.ioloop.IOLoop.instance().start()

    else:
        app.run('localhost', cfg['port'])


def run_tornado(app, cfg):
    _configure_logging(app.logger, cfg.get('logging', {}), 'tornado')
    import tornado.wsgi
    import tornado.httpserver
    import tornado.ioloop

    http_server = tornado.httpserver.HTTPServer(tornado.wsgi.WSGIContainer(app))
    http_server.listen(cfg['port'])
    tornado.ioloop.IOLoop.instance().start()


def run_werkzeug(app, cfg, reloading=True):
    _configure_logging(app.logger, cfg.get('logging', {}), 'werkzeug')
    import werkzeug.serving

    if reloading:
        werkzeug.serving.run_simple(
            'localhost',
            cfg['port'],
            app,
            use_reloader=True,
            extra_files=watched_files
        )
    else:
        werkzeug.serving.run_simple(
            'localhost',
            cfg['port'],
            app
        )


def _configure_logging(app_logger, log_cfg, webserver):
    loggers = _configure_webserver_loggers(webserver) + [app_logger]
    for l in loggers:
        l.setLevel(logging.DEBUG)

    c = logging.config.BaseConfigurator({})
    f = logging.Formatter(
        fmt=log_cfg.get('format', '[%(asctime)s][%(name)s][%(levelname)s] %(message)s'),
        datefmt=log_cfg.get('datefmt', '%Y-%b-%d %H:%M:%S')
    )
    h_classes = {
        'stream_handlers': logging.StreamHandler,
        'timed_rotating_file_handlers': logging.handlers.TimedRotatingFileHandler
    }

    for handler_type in ('stream_handlers', 'timed_rotating_file_handlers'):
        for h in log_cfg.get(handler_type, []):
            if 'stream' in h:
                h['stream'] = c.convert(h['stream'])

            level = logging.getLevelName(h.pop('level', 'WARNING'))
            handler = h_classes[handler_type](**h)
            handler.setFormatter(f)
            handler.setLevel(level)
            for l in loggers:
                l.addHandler(handler)


def _configure_webserver_loggers(webserver):
    if webserver == 'werkzeug':
        import werkzeug._internal
        # werkzeug's default logger is None until werkzeug._default._log is called. Initialise it to a
        # logging.Logger here, and set it
        werkzeug._internal._logger = logging.getLogger('werkzeug')
        werkzeug._internal._logger.setLevel(logging.DEBUG)
        return [werkzeug._internal._logger]

    elif webserver == 'tornado':
        import tornado.log
        return [tornado.log.access_log, tornado.log.app_log, tornado.log.gen_log]

    else:
        raise AssertionError("webserver %s should be one of 'werkzeug' or 'tornado'" % webserver)


def main():
    for module, cfg in ((rest_api, rest_config)):#, (reporting_app, reporting_app_config)):
        # p = multiprocessing.Process(target=run_werkzeug, args=(module.app, cfg))
        # p.start()
        run_werkzeug(module.app, cfg)


if __name__ == '__main__':
    main()
