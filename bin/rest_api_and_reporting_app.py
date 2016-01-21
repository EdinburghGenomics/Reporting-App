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

import werkzeug._internal
# override werkzeug's default logger
werkzeug._internal._logger = logging.getLogger('werkzeug')
werkzeug._internal._logger.setLevel(logging.DEBUG)


def run_app(app, cfg):
    app.debug = cfg.get('debug', False)
    _configure_logging(app.logger, cfg.get('logging', {}))

    if cfg['tornado']:
        import tornado.wsgi
        import tornado.httpserver
        import tornado.ioloop

        # TODO: configure Tornado logging

        http_server = tornado.httpserver.HTTPServer(tornado.wsgi.WSGIContainer(app))
        http_server.listen(cfg['port'])
        tornado.ioloop.IOLoop.instance().start()

    else:
        app.run('localhost', cfg['port'])


def _configure_logging(logger, log_cfg):
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
            werkzeug._internal._logger.addHandler(handler)
            logger.addHandler(handler)


def main():
    for module, cfg in ((rest_api, rest_config), (reporting_app, reporting_app_config)):
        p = multiprocessing.Process(target=run_app, args=(module.app, cfg))
        p.start()


if __name__ == '__main__':
    main()
