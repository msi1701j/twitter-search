#!/usr/bin/env python3
# -*- cofing: utf-8 -*-
"""TwsConfig Test Unit"""

import os, sys
import unittest

import logging

DIR_BASE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(DIR_BASE, '..'))
sys.path.insert(0, os.path.join(DIR_BASE, '../lib'))
sys.path.insert(0, os.path.join(DIR_BASE, '../..'))
sys.path.insert(0, os.path.join(DIR_BASE,'../../lib'))

from tslib import Tweets
from tslib import TwsConfig
from tslib import ts_dateutils

GETID_ENDPOINT = "https://api.twitter.com/1.1/statuses/show.json"

class TestTweets(unittest.TestCase):
    """Tweets の unittest"""

    def setUp(self):
        argparams = {}
        self.config = TwsConfig(argparams)
        self.config['dryrun'] = False
       

    def test_001(self):
        pass

if __name__ == "__main__":
    unittest.main()
