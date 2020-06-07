# -*- codign: utf-8 -*-

import unittest
from test.support import captured_stdout
import sys
import os
import re
import copy
import json
import tempfile

DIR_BASE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(DIR_BASE, '..'))
sys.path.insert(0, os.path.join(DIR_BASE, '../lib'))
sys.path.insert(0, os.path.join(DIR_BASE, '../..'))
sys.path.insert(0, os.path.join(DIR_BASE,'../../lib'))

import twsearch
from tslib import TwsConfig
#from tslib import 

GETID_ENDPOINT = "https://api.twitter.com/1.1/statuses/show.json"
GETID_FAMILY = "statuses"
GETID_RESOURCE = "statuses/show"

SAMPLE_ID="1233343419176480769"

RE_VALNUM = re.compile(r'(?P<target>"(statuses_count|favorite_count|favourites_count|friends_count|followers_count)":\s*)\d+')

TWEET_CONTENT_PREFIX = r"""{
"""
TWEET_ADDTIONAL_PREFIX = r"""{
  "created_time": 1582886960,
  "base": {
    "created_at": "Fri Feb 28 10:49:20 +0000 2020",
    "created_at_exceltime": 43889.45092592593,
    "created_at_epoch": 1582886960,
    "created_at_jst": "2020-02-28 19:49:20 JST"
  },
  "tweet": {
"""

TWEET_CONTENT = r"""  "created_at": "Fri Feb 28 10:49:20 +0000 2020",
    "id": 1233343419176480769,
    "id_str": "1233343419176480769",
    "full_text": "なんか、デマ情報に踊らされてトイレットペーパーがオイルショック並みになってるのを見て、銀行の取り付け騒ぎとかも起こるんじゃないかと不安になってくるね。\n\n本当に必要な人の手には渡らないという……\n\nみんな、ここは一旦、落ち着こう。",
    "truncated": false,
    "display_text_range": [
      0,
      115
    ],
    "entities": {
      "hashtags": [],
      "symbols": [],
      "user_mentions": [],
      "urls": []
    },
    "source": "<a href=\"http://twitter.com/download/android\" rel=\"nofollow\">Twitter for Android</a>",
    "in_reply_to_status_id": null,
    "in_reply_to_status_id_str": null,
    "in_reply_to_user_id": null,
    "in_reply_to_user_id_str": null,
    "in_reply_to_screen_name": null,
    "user": {
      "id": 14963504,
      "id_str": "14963504",
      "name": "五十嵐智(いかちょー)",
      "screen_name": "Ikarashi",
      "location": "埼玉県さいたま市",
      "description": "ケロロフリーク、SFファン、CISSP、産業カウンセラー、キャリアコンサルティング技能士(2級)、国家資格登録キャリアコンサルタント。通称:いかちょー、筆名:ほりえみつお。",
      "url": "https://t.co/rNzDugMRlT",
      "entities": {
        "url": {
          "urls": [
            {
              "url": "https://t.co/rNzDugMRlT",
              "expanded_url": "http://ameblo.jp/vsa-v",
              "display_url": "ameblo.jp/vsa-v",
              "indices": [
                0,
                23
              ]
            }
          ]
        },
        "description": {
          "urls": []
        }
      },
      "protected": false,
      "followers_count": 1001,
      "friends_count": 2281,
      "listed_count": 82,
      "created_at": "Sat May 31 14:38:14 +0000 2008",
      "favourites_count": 10401,
      "utc_offset": null,
      "time_zone": null,
      "geo_enabled": true,
      "verified": false,
      "statuses_count": 36201,
      "lang": null,
      "contributors_enabled": false,
      "is_translator": false,
      "is_translation_enabled": false,
      "profile_background_color": "9AE4E8",
      "profile_background_image_url": "http://abs.twimg.com/images/themes/theme1/bg.png",
      "profile_background_image_url_https": "https://abs.twimg.com/images/themes/theme1/bg.png",
      "profile_background_tile": true,
      "profile_image_url": "http://pbs.twimg.com/profile_images/2175916038/ikacho-100x100_normal.png",
      "profile_image_url_https": "https://pbs.twimg.com/profile_images/2175916038/ikacho-100x100_normal.png",
      "profile_banner_url": "https://pbs.twimg.com/profile_banners/14963504/1398595872",
      "profile_link_color": "C27DFA",
      "profile_sidebar_border_color": "2200FF",
      "profile_sidebar_fill_color": "DED9FF",
      "profile_text_color": "000000",
      "profile_use_background_image": true,
      "has_extended_profile": true,
      "default_profile": false,
      "default_profile_image": false,
      "following": null,
      "follow_request_sent": null,
      "notifications": null,
      "translator_type": "none"
    },
    "geo": null,
    "coordinates": null,
    "place": null,
    "contributors": null,
    "is_quote_status": false,
    "retweet_count": 1,
    "favorite_count": 10,
    "favorited": false,
    "retweeted": false,
    "lang": "ja"
"""
TWEET_CONTENT_POSTFIX = r"""}
"""
TWEET_ADDITIONAL_POSTFIX = r"""  },
  "search_metadata": {},
  "wakati": {
    "text": "なんか 、 デマ 情報 に 踊ら さ れ て トイレットペーパー が オイルショック 並み に なっ てる の を 見 て 、 銀行 の 取り付け 騒ぎ とか も 起こる ん じゃ ない か と 不安 に なっ て くる ね 。   本当に 必要 な 人 の 手 に は 渡ら ない という … …   みんな 、 ここ は 一旦 、 落ち着こ う 。"
  }
}
"""

CSV_PREFIX = "\ufeff"
CSV_HEADER = r""""created_at_exceltime","created_at_epoch","created_at","created_at_jst","text","extended_text","hashtags","id","userId","name","screen_name","fixlink","wakati_text","wakati_extended_text"
"""
CSV_CONTENT = r""""43889.45092592593","1582886960","Fri Feb 28 10:49:20 +0000 2020","2020-02-28 19:49:20 JST","なんか、デマ情報に踊らされてトイレットペーパーがオイルショック並みになってるのを見て、銀行の取り付け騒ぎとかも起こるんじゃないかと不安になってくるね。

本当に必要な人の手には渡らないという……

みんな、ここは一旦、落ち着こう。","","","1233343419176480769","14963504","五十嵐智(いかちょー)","Ikarashi","https://twitter.com/Ikarashi/status/1233343419176480769","なんか 、 デマ 情報 に 踊ら さ れ て トイレットペーパー が オイルショック 並み に なっ てる の を 見 て 、 銀行 の 取り付け 騒ぎ とか も 起こる ん じゃ ない か と 不安 に なっ て くる ね 。   本当に 必要 な 人 の 手 に は 渡ら ない という … …   みんな 、 ここ は 一旦 、 落ち着こ う 。",""
"""

def set_sys_args(*args):
    del sys.argv[:]
    sys.argv.append('prog') # argv[0]
    for arg in args:
        sys.argv.append(arg)
    return TwsConfig(twsearch.tw_argparse())


class TestTwSearchWakati(unittest.TestCase):
    """--wakati オプションのテスト"""
    def setUp(self):
        self.sys_argv = copy.deepcopy(sys.argv)

    def tearDown(self):
        del sys.argv[:]
        sys.argv = copy.deepcopy(self.sys_argv)

    def test_wakati_001(self):
        """--wakati オプションによる分かち書きテスト"""
        config = set_sys_args('--wakati', '-i', SAMPLE_ID, '-o', '-')
        splunk_writer = twsearch.SplunkWriterBySearch(config)
        res_j = splunk_writer.get_one_tweet()
        lines = json.dumps(res_j, indent=2, ensure_ascii=False).splitlines()
        tc_lines = (TWEET_CONTENT_PREFIX + TWEET_CONTENT
                    + TWEET_CONTENT_POSTFIX).splitlines()
        for i, line in enumerate(lines):
            tc_line = tc_lines[i]
            line = RE_VALNUM.sub(r'\g<target>N', line).strip()
            tc_line = RE_VALNUM.sub(r'\g<target>N', tc_line).strip()
            self.assertEqual(line, tc_line)
        del res_j
        del splunk_writer
        del config

    def test_wakati_002(self):
        """--wakati オプションによる分かち書きテスト(CSV)"""
        outputfilename = tempfile.gettempprefix() + '.csv'
        if os.path.exists(outputfilename):
            os.remove(outputfilename)
        config = set_sys_args('--wakati', '-i', SAMPLE_ID, '-o', outputfilename)
        splunk_writer = twsearch.SplunkWriterBySearch(config)
        splunk_writer.generate(config)
        splunk_writer.flush()
        del splunk_writer
        with open(outputfilename, 'r', newline='', encoding='utf_8') as infile:
            infile_lines = infile.read()
        lines = infile_lines.splitlines()
        tc_lines = (CSV_PREFIX + CSV_CONTENT).splitlines()
        for i, line in enumerate(lines):
            line = RE_VALNUM.sub(r'\g<target>N', line).strip()
            try:
                tc_line = tc_lines[i]
            except IndexError:
                print(f'i:{i}, line:{line}', file=sys.stderr)
                raise IndexError
            tc_line = RE_VALNUM.sub(r'\g<target>N', tc_line).strip()
            self.assertEqual(line, tc_line)
        os.remove(outputfilename)
        del config

    def test_wakati_003(self):
        """--wakati オプションによる分かち書き追記テスト(CSV)"""
        outputfilename = tempfile.gettempprefix() + '.csv'
        if os.path.exists(outputfilename):
            os.remove(outputfilename)
        config = set_sys_args('--wakati', '-i', SAMPLE_ID, '-o', outputfilename)
        splunk_writer = twsearch.SplunkWriterBySearch(config)
        splunk_writer.generate(config)
        splunk_writer.flush()
        del splunk_writer
        config = set_sys_args('--wakati', '-i', SAMPLE_ID, '-o', outputfilename)
        splunk_writer = twsearch.SplunkWriterBySearch(config)
        splunk_writer.generate(config)
        splunk_writer.flush()
        del splunk_writer
        with open(outputfilename, 'r', newline='', encoding='utf_8') as infile:
            infile_lines = infile.read()
        lines = infile_lines.splitlines()
        tc_lines = (CSV_PREFIX + CSV_CONTENT + CSV_CONTENT).splitlines()
        for i, line in enumerate(lines):
            line = RE_VALNUM.sub(r'\g<target>N', line).strip()
            try:
                tc_line = tc_lines[i]
            except IndexError:
                print(f'i:{i}, line:{line}', file=sys.stderr)
                raise IndexError
            tc_line = RE_VALNUM.sub(r'\g<target>N', tc_line).strip()
            self.assertEqual(line, tc_line)
        os.remove(outputfilename)
        del config

    def test_wakati_004(self):
        """--wakati オプションによる分かち書き追記テスト(CSV ヘッダ付き)"""
        outputfilename = tempfile.gettempprefix() + '.csv'
        if os.path.exists(outputfilename):
            os.remove(outputfilename)
        config = set_sys_args('--wakati', '-i', SAMPLE_ID, '-w', '-o', outputfilename)
        splunk_writer = twsearch.SplunkWriterBySearch(config)
        splunk_writer.generate(config)
        splunk_writer.flush()
        del splunk_writer
        with open(outputfilename, 'r', newline='', encoding='utf_8') as infile:
            infile_lines = infile.read()
        lines = infile_lines.splitlines()
        tc_lines = (CSV_PREFIX + CSV_HEADER + CSV_CONTENT).splitlines()
        for i, line in enumerate(lines):
            line = RE_VALNUM.sub(r'\g<target>N', line).strip()
            try:
                tc_line = tc_lines[i]
            except IndexError:
                print(f'i:{i}, line:{line}', file=sys.stderr)
                raise IndexError
            tc_line = RE_VALNUM.sub(r'\g<target>N', tc_line).strip()
            self.assertEqual(line, tc_line)
        os.remove(outputfilename)
        del config

    def test_wakati_005(self):
        """--wakati オプションによる分かち書きテスト(JSON)"""
        outputfilename = tempfile.gettempprefix() + '.json'
        if os.path.exists(outputfilename):
            os.remove(outputfilename)
        config = set_sys_args('--wakati', '-i', SAMPLE_ID, '-j', '-o', outputfilename)
        splunk_writer = twsearch.SplunkWriterBySearch(config)
        splunk_writer.generate(config)
        splunk_writer.flush()
        del splunk_writer
        with open(outputfilename, 'r', newline='', encoding='utf_8') as infile:
            infile_lines = infile.read()
        lines = infile_lines.splitlines()
        tc_lines = (TWEET_ADDTIONAL_PREFIX + TWEET_CONTENT
                    + TWEET_ADDITIONAL_POSTFIX).splitlines()
        for i, line in enumerate(lines):
            line = RE_VALNUM.sub(r'\g<target>N', line).strip()
            try:
                tc_line = tc_lines[i]
            except IndexError:
                print(f'i:{i}, line:{line}', file=sys.stderr)
                raise IndexError
            tc_line = RE_VALNUM.sub(r'\g<target>N', tc_line).strip()
            self.assertEqual(line, tc_line)
        os.remove(outputfilename)
        del config



if __name__ == "__main__":
    unittest.main()
