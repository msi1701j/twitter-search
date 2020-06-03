#!/usr/bin/env python3
# -*- cofing: utf-8 -*-
"""TwsConfig Test Unit"""

import os, sys
import unittest

DIR_BASE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(DIR_BASE, '..'))
sys.path.insert(0, os.path.join(DIR_BASE, '../lib'))
sys.path.insert(0, os.path.join(DIR_BASE, '../..'))
sys.path.insert(0, os.path.join(DIR_BASE,'../../lib'))

from tslib import TwsConfig

class TestTwsConfig(unittest.TestCase):
    """TwsConfig の unittest"""

    def setUp(self):
        argparams = dict()
        argparams['search_string'] = "dummy_search_string"
        self.config = TwsConfig(argparams)

    def test_001(self):
        """search string のテスト"""
        self.assertEqual(self.config['search_string'], 'dummy_search_string')


class TestTwsConfigAlt(unittest.TestCase):
    """TwsConfig の unittest (alternative)"""
    def setUp(self):
        argparams = dict()
        argparams['search_string'] = "dummy_search_string1 dummy_search_string2"
        self.config = TwsConfig(argparams)

    def test_101(self):
        """search string のテスト 101"""
        self.assertEqual(self.config['search_string'],
                         'dummy_search_string1 dummy_search_string2')


if __name__ == "__main__":
    unittest.main()
