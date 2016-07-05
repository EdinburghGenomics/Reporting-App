import os
import logging
import egcg_core.config
from egcg_core.app_logging import logging_default as log_cfg


def main():
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from reporting_app import app
    from config import reporting_app_config as cfg

    app.debug = cfg.get('debug', False)

    egcg_core.config.cfg.load_config_file(os.getenv('REPORTINGCONFIG'))
    log_cfg.loggers['app'] = app.logger
    app.logger.setLevel(logging.DEBUG)
    log_cfg.configure_handlers_from_config()

    return app


if __name__ == '__main__':
    application = main()
