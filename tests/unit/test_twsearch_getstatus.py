# -*- codign: utf-8 -*-

import unittest
from test.support import captured_stdout
import sys
import os
import re
import copy

DIR_BASE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(DIR_BASE, '..'))
sys.path.insert(0, os.path.join(DIR_BASE, '../lib'))
sys.path.insert(0, os.path.join(DIR_BASE, '../..'))
sys.path.insert(0, os.path.join(DIR_BASE,'../../lib'))

import twsearch
from tslib import TwsConfig

RE_REMAIN = re.compile(r'(?P<target>"{0,1}remaining"{0,1}:\s*)\d{1,3}')
RE_RESET = re.compile(r'(?P<target>"{0,1}reset"{0,1}:\s*)\d{10}')
RE_DATETIME = re.compile(r'(?P<target>reset\(epoch2datetime\):\s*).*$')

def set_sys_args(*args):
    del sys.argv[:]
    sys.argv.append('prog') # argv[0]
    for arg in args:
        sys.argv.append(arg)
    sys.argv.append('query')    # argv[-1]
    return TwsConfig(twsearch.tw_argparse())


class TestTwSearchGetStatus(unittest.TestCase):
    """Rate Limit ステータス情報取得のテスト"""
    def setUp(self):
        self.sys_argv = copy.deepcopy(sys.argv)

    def tearDown(self):
        del sys.argv[:]
        sys.argv = copy.deepcopy(self.sys_argv)

#    @unittest.expectedFailure
    def test_disp_limit_status_001(self):
        """-g オプションによるdisp_limit_status() テスト"""
        config = set_sys_args('-g')
        splunk_writer = twsearch.SplunkWriterBySearch(config=config)
        with captured_stdout() as stdout:
            splunk_writer.disp_limit_status()
            lines = stdout.getvalue().splitlines()

        limit_status_string = """{
  "rate_limit_context": {
    "application": "dummykey"
  },
  "resources": {
    "search": {
      "/search/tweets": {
        "limit": 450,
        "remaining": 447,
        "reset": 1591085881
      }
    }
  }
}
limit: 450
remaining: 447
reset: 1591085881
reset(epoch2datetime): 2020-06-02 17:18:01
"""
        lss_lines = limit_status_string.splitlines()
        for i, line in enumerate(lines):
            line = RE_REMAIN.sub(r'\g<target>N', line)
            lss_lines[i] = RE_REMAIN.sub(r'\g<target>N', lss_lines[i])
            line = RE_RESET.sub(r'\g<target>N', line)
            lss_lines[i] = RE_RESET.sub(r'\g<target>N', lss_lines[i])
            line = RE_DATETIME.sub(r'\g<target>N', line)
            lss_lines[i] = RE_DATETIME.sub(r'\g<target>N', lss_lines[i])
            self.assertEqual(line, lss_lines[i])
        del splunk_writer
        del config


if __name__ == "__main__":
    unittest.main()
