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

def set_sys_args(*args):
    del sys.argv[:]
    sys.argv.append('prog') # argv[0]
    for arg in args:
        sys.argv.append(arg)
    sys.argv.append('query')    # argv[-1]
    return TwsConfig(twsearch.tw_argparse())


class TestTwSearchArgs(unittest.TestCase):
    """コマンドライン引数のテスト"""
    def setUp(self):
        self.sys_argv = copy.deepcopy(sys.argv)

    def test_argtest_001(self):
        """search_string オプション&オプションデフォルト値テスト"""
        config = set_sys_args()
        self.assertEqual(config['search_string'], 'query')
        self.assertFalse(config['getstatus'])
        self.assertFalse(config['localno'])
        self.assertEqual(config['dispcount'], -1)
        self.assertEqual(config['count'], 100)
        self.assertIsNone(config['since_id'])
        self.assertIsNone(config['max_id'])
        self.assertIsNone(config['since_date'])
        self.assertIsNone(config['max_date'])
        self.assertEqual(config['retry_max'], 5)
        self.assertEqual(config['shelvefile'], 'twsearch.shelve')
        self.assertEqual(config['shelve_flag'], 'c')
        self.assertEqual(config['outputfile'], 'twsearch.csv')
        self.assertFalse(config['outputfile_reset'])
        self.assertEqual(config['output_mode'], 'a')
        self.assertFalse(config['write_header'])
        self.assertFalse(config['write_json'])
        self.assertIsNone(config['search_id'])
        self.assertEqual(config['configfile'], 'twsearch.ini')
        self.assertIsNone(config['dummy'])
        self.assertFalse(config['dryrun'])
        self.assertFalse(config['verbose'])
        self.assertFalse(config['silence'])
        self.assertFalse(config['debug'])
        del config
        sys.argv = copy.deepcopy(self.sys_argv)
            
    def test_argtest_002(self):
        """-g (getstatus) オプションテスト"""
        config = set_sys_args('-g')
        self.assertTrue(config['getstatus'])
        del config
        sys.argv = copy.deepcopy(self.sys_argv)

    def test_argtest_003(self):
        """-l (localno) オプションテスト"""
        config = set_sys_args('-l')
        self.assertTrue(config['localno'])
        del config
        sys.argv = copy.deepcopy(self.sys_argv)
        
    def test_argtest_004(self):
        """-c (dispcount) オプションテスト"""
        config = set_sys_args('-c', '10')
        self.assertEqual(config['dispcount'], 10)
        del config
        sys.argv = copy.deepcopy(self.sys_argv)
        
    def test_argtest_005(self):
        """-C (count) オプションテスト"""
        config = set_sys_args('-C', '10')
        self.assertEqual(config['count'], 10)
        del config
        sys.argv = copy.deepcopy(self.sys_argv)
        
    def test_argtest_006(self):
        """-S (since_id) オプションテスト"""
        config = set_sys_args('-S', '1234567890')
        self.assertEqual(config['since_id'], '1234567890')
        del config
        sys.argv = copy.deepcopy(self.sys_argv)
        
    def test_argtest_007(self):
        """-M (max_id) オプションテスト"""
        config = set_sys_args('-M', '1234567890')
        self.assertEqual(config['max_id'], '1234567890')
        del config
        sys.argv = copy.deepcopy(self.sys_argv)
        
    def test_argtest_008(self):
        """--since_date オプションテスト"""
        config = set_sys_args('--since_date', '2020-01-01')
        self.assertEqual(config['since_date'], '2020-01-01')
        del config
        sys.argv = copy.deepcopy(self.sys_argv)

    def test_argtest_009(self):
        """--max_date オプションテスト"""
        config = set_sys_args('--max_date', '2020-01-01')
        self.assertEqual(config['max_date'], '2020-01-01')
        del config
        sys.argv = copy.deepcopy(self.sys_argv)

    def test_argtest_010(self):
        """-t (--retry_max) オプションテスト"""
        config = set_sys_args('-t', '10')
        self.assertEqual(config['retry_max'], 10)
        del config
        sys.argv = copy.deepcopy(self.sys_argv)

    def test_argtest_011(self):
        """-b (--shelvefile) オプションテスト"""
        config = set_sys_args('-b', 'shelve_test.shelve')
        self.assertEqual(config['shelvefile'], 'shelve_test.shelve')
        del config
        sys.argv = copy.deepcopy(self.sys_argv)

    def test_argtest_012(self):
        """-B (--shelve_reset) オプションテスト"""
        config = set_sys_args('-B')
        self.assertEqual(config['shelve_flag'], 'n')
        del config
        sys.argv = copy.deepcopy(self.sys_argv)

    def test_argtest_013(self):
        """-o (--outputfile) オプションテスト"""
        config = set_sys_args('-o', 'outputfile_test.out')
        self.assertEqual(config['outputfile'], 'outputfile_test.out')
        del config
        sys.argv = copy.deepcopy(self.sys_argv)

    def test_argtest_014(self):
        """-O (--outputfile_reset) オプションテスト"""
        config = set_sys_args('-O')
        self.assertTrue(config['outputfile_reset'])
        self.assertEqual(config['output_mode'], 'w')
        del config
        sys.argv = copy.deepcopy(self.sys_argv)

    def test_argtest_015(self):
        """-w (--write_header) オプションテスト"""
        config = set_sys_args('-w')
        self.assertTrue(config['write_header'])
        del config
        sys.argv = copy.deepcopy(self.sys_argv)

    def test_argtest_016(self):
        """-j (--write_json) オプションテスト"""
        config = set_sys_args('-j')
        self.assertTrue(config['write_json'])
        self.assertEqual(config['outputfile'], 'twsearch.json')
        del config
        sys.argv = copy.deepcopy(self.sys_argv)

    def test_argtest_017(self):
        """-i (--id) オプションテスト"""
        config = set_sys_args('-i', '1234567890')
        self.assertEqual(config['search_id'], '1234567890')
        del config
        sys.argv = copy.deepcopy(self.sys_argv)

    def test_argtest_018(self):
        """-I (--inifile) オプションテスト"""
        config = set_sys_args('-I', 'inifile_test.ini')
        self.assertEqual(config['configfile'], 'inifile_test.ini')
        del config
        sys.argv = copy.deepcopy(self.sys_argv)

    def test_argtest_019(self):
        """-f (--dummy) オプションテスト"""
        config = set_sys_args('-f')
        self.assertIsNone(config['dummy'])
        del config
        sys.argv = copy.deepcopy(self.sys_argv)

    def test_argtest_020(self):
        """-d (--dryrun) オプションテスト"""
        config = set_sys_args('-d')
        self.assertTrue(config['dryrun'])
        del config
        sys.argv = copy.deepcopy(self.sys_argv)

    def test_argtest_021(self):
        """-v (--verbose) オプションテスト"""
        config = set_sys_args('-v')
        self.assertTrue(config['verbose'])
        del config
        sys.argv = copy.deepcopy(self.sys_argv)

    def test_argtest_022(self):
        """-s (--silence) オプションテスト"""
        config = set_sys_args('-s')
        self.assertTrue(config['silence'])
        del config
        sys.argv = copy.deepcopy(self.sys_argv)

    def test_argtest_023(self):
        """-D (--debug) オプションテスト"""
        config = set_sys_args('-D')
        self.assertTrue(config['debug'])
        del config
        sys.argv = copy.deepcopy(self.sys_argv)


if __name__ == "__main__":
    unittest.main()
