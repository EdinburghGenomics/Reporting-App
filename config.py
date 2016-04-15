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

    def query(self, *parts, top_level=None, ret_default=None):
        if top_level is None:
            top_level = self
        item = None

        for p in parts:
            item = top_level.get(p)
            if item:
                top_level = item
            else:
                return ret_default
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


class ColumnMappingConfig(Configuration):
    def __init__(self, env_config, home_config, etc_config):
        super().__init__(env_config, home_config, etc_config)

        self.column_def = self.content.pop('column_def')
        self.default_values = self.content.pop('default_values', [])
        for key in self.content:
            #self.content[key] needs to be a list of string or dictionaries
            for i in range(len(self.content[key])):
                if isinstance(self.content[key][i], str):
                    if self.content[key][i] in self.column_def:
                        self.content[key][i] = self.column_def[self.content[key][i]]
                    else:
                        raise ReferenceError('%s is not referenced in the column definition from the column mapping config'%self.content[key][i])
                elif isinstance(self.content[key][i], dict):
                    if self.content[key][i]['column_def'] in self.column_def:
                        self.content[key][i].update(self.column_def[self.content[key][i]['column_def']])
                    else:
                        #leave the definition as it is
                        pass
                self._set_defaults(self.content[key][i])

    def _set_defaults(self, column_def):
        for k in self.default_values:
            if k not in column_def:
                column_def[k] = self.default_values[k]


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
schema = Configuration('REPORTINGSCHEMA', '~/.reporting_schema.yaml', 'schema.yaml')
col_mappings = ColumnMappingConfig('REPORTINGCOLS', '~/.reporting_cols.yaml', 'column_mappings.yaml')
