__author__ = 'mwham'
from unittest import TestCase
import os.path


class Helper(TestCase):
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
