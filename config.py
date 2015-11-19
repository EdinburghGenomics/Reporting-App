__author__ = 'mwham'
import os
import yaml


class Configuration:
    def __init__(self, app_type):
        self.content = yaml.load(open(self._find_config_file(), 'r'))[app_type]

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

    @staticmethod
    def _find_config_file():
        for config in (
                os.getenv('REPORTINGCONFIG'),
                os.path.expanduser('~/.reporting.yaml'),
                os.path.join(os.path.abspath(os.path.dirname(__file__)), 'etc', 'example_reporting.yaml')
        ):
            if config and os.path.isfile(config):
                return config

        raise FileNotFoundError('Could not find config file')

    def __getitem__(self, item):
        return self.content[item]


reporting_app_config = Configuration('reporting_app')
rest_config = Configuration('rest_app')
schema = yaml.load(
    open(
        os.path.join(
            os.path.abspath(
                os.path.dirname(__file__)
            ),
            'etc',
            'schemas.yaml'
        )
    )
)
col_mappings = yaml.load(
    open(
        os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'etc',
            'column_mappings.yaml'
        )
    )
)
