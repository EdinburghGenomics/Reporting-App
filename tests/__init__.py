from os.path import dirname, abspath, join
from unittest import TestCase


class Helper(TestCase):
    top_level = dirname(dirname(abspath(__file__)))
    assets_dir = join(top_level, 'tests', 'assets')
    config_file = join(top_level, 'etc', 'example_reporting.yaml')
