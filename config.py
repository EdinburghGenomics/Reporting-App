__author__ = 'mwham'
import os
import yaml


class Configuration:
    def __init__(self, env_config, home_config, etc_config):
        self.env_config = env_config
        self.home_config = home_config
        self.etc_config = etc_config

        self.content = self._load_config_file()

    def get(self, item, ret_default=None):
        try:
            return self[item]
        except KeyError:
            return ret_default

    def query(self, *parts, top_level=None):
        if top_level is None:
            top_level = self
        item = None

        for p in parts:
            item = top_level.get(p)
            if item:
                top_level = item
            else:
                return None
        return item

    def _load_config_file(self):
        return yaml.load(open(self._find_config_file(), 'r'))

    def _find_config_file(self):
        for config in (
                os.getenv(self.env_config),
                os.path.expanduser(self.home_config),
                os.path.join(os.path.abspath(os.path.dirname(__file__)), 'etc', self.etc_config)
        ):
            if config and os.path.isfile(config):
                return config

        raise FileNotFoundError('Could not find config file')

    def __getitem__(self, item):
        return self.content[item]


class SplitConfiguration(Configuration):
    def __init__(self, env_config, home_config, etc_config, app_type):
        self.app_type = app_type
        super().__init__(env_config, home_config, etc_config)

    def _load_config_file(self):
        env = os.getenv('REPORTINGENV', 'default')
        return yaml.load(open(self._find_config_file(), 'r'))[env][self.app_type]



reporting_app_config = SplitConfiguration(
    'REPORTINGCONFIG',
    '~/.reporting.yaml',
    'example_reporting.yaml',
    'reporting_app'
)
rest_config = SplitConfiguration(
    'REPORTINGCONFIG',
    '~/.reporting.yaml',
    'example_reporting.yaml',
    'rest_app'
)
schema = Configuration('REPORTINGSCHEMA', '.reporting_schema.yaml', 'schema.yaml')
col_mappings = Configuration('REPORTINGCOLS', '.reporting_cols.yaml', 'column_mappings.yaml')
