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

RE_VALNUM = re.compile(r'(?P<target>"(statuses_count|favorite_count|favourites_count|friends_count|followers_count)":\s*)\d+')

TWEET_CONTENT_PREFIX = """{
"""
TWEET_ADDTIONAL_PREFIX = """{
  "created_time": 1591232401,
  "base": {
    "created_at": "Thu Jun 04 01:00:01 +0000 2020",
    "created_at_exceltime": 43986.04167824074,
    "created_at_epoch": 1591232401,
    "created_at_jst": "2020-06-04 10:00:01 JST"
  },
  "tweet": {
"""
TWEET_CONTENT = """  "created_at": "Thu Jun 04 01:00:01 +0000 2020",
  "id": 1268346734951964672,
  "id_str": "1268346734951964672",
  "full_text": "ずいぶん前に作ったロゴ。\\n#ロゴ #五十嵐家 #logo https://t.co/3xHgegtckl",
  "truncated": false,
  "display_text_range": [
    0,
    28
  ],
  "entities": {
    "hashtags": [
      {
        "text": "ロゴ",
        "indices": [
          13,
          16
        ]
      },
      {
        "text": "五十嵐家",
        "indices": [
          17,
          22
        ]
      },
      {
        "text": "logo",
        "indices": [
          23,
          28
        ]
      }
    ],
    "symbols": [],
    "user_mentions": [],
    "urls": [],
    "media": [
      {
        "id": 1268346600008507392,
        "id_str": "1268346600008507392",
        "indices": [
          29,
          52
        ],
        "media_url": "http://pbs.twimg.com/media/EZoSg0GU4AAXUe8.jpg",
        "media_url_https": "https://pbs.twimg.com/media/EZoSg0GU4AAXUe8.jpg",
        "url": "https://t.co/3xHgegtckl",
        "display_url": "pic.twitter.com/3xHgegtckl",
        "expanded_url": "https://twitter.com/Ikarashi/status/1268346734951964672/photo/1",
        "type": "photo",
        "sizes": {
          "thumb": {
            "w": 116,
            "h": 116,
            "resize": "crop"
          },
          "small": {
            "w": 323,
            "h": 116,
            "resize": "fit"
          },
          "medium": {
            "w": 323,
            "h": 116,
            "resize": "fit"
          },
          "large": {
            "w": 323,
            "h": 116,
            "resize": "fit"
          }
        }
      }
    ]
  },
  "extended_entities": {
    "media": [
      {
        "id": 1268346600008507392,
        "id_str": "1268346600008507392",
        "indices": [
          29,
          52
        ],
        "media_url": "http://pbs.twimg.com/media/EZoSg0GU4AAXUe8.jpg",
        "media_url_https": "https://pbs.twimg.com/media/EZoSg0GU4AAXUe8.jpg",
        "url": "https://t.co/3xHgegtckl",
        "display_url": "pic.twitter.com/3xHgegtckl",
        "expanded_url": "https://twitter.com/Ikarashi/status/1268346734951964672/photo/1",
        "type": "photo",
        "sizes": {
          "thumb": {
            "w": 116,
            "h": 116,
            "resize": "crop"
          },
          "small": {
            "w": 323,
            "h": 116,
            "resize": "fit"
          },
          "medium": {
            "w": 323,
            "h": 116,
            "resize": "fit"
          },
          "large": {
            "w": 323,
            "h": 116,
            "resize": "fit"
          }
        }
      }
    ]
  },
  "source": "<a href=\\"https://mobile.twitter.com\\" rel=\\"nofollow\\">Twitter Web App</a>",
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
    "followers_count": 1000,
    "friends_count": 2282,
    "listed_count": 82,
    "created_at": "Sat May 31 14:38:14 +0000 2008",
    "favourites_count": 10386,
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
  "retweet_count": 0,
  "favorite_count": 0,
  "favorited": false,
  "retweeted": false,
  "possibly_sensitive": false,
  "possibly_sensitive_appealable": false,
  "lang": "ja"
"""
TWEET_CONTENT_POSTFIX ="""}
"""
TWEET_ADDITIONAL_POSTFIX="""  },
  "search_metadata": {}
}
"""

CSV_PREFIX="\ufeff"
CSV_HEADER=""""created_at_exceltime","created_at_epoch","created_at","created_at_jst","text","extended_text","hashtags","id","userId","name","screen_name","fixlink","wakati_text","wakati_extended_text"
"""
CSV_CONTENT=""""43986.04167824074","1591232401","Thu Jun 04 01:00:01 +0000 2020","2020-06-04 10:00:01 JST","ずいぶん前に作ったロゴ。
#ロゴ #五十嵐家 #logo https://t.co/3xHgegtckl","","ロゴ,五十嵐家,logo","1268346734951964672","14963504","五十嵐智(いかちょー)","Ikarashi","https://twitter.com/Ikarashi/status/1268346734951964672","",""
"""

def set_sys_args(*args):
    del sys.argv[:]
    sys.argv.append('prog') # argv[0]
    for arg in args:
        sys.argv.append(arg)
    return TwsConfig(twsearch.tw_argparse())


class TestTwSearchGetOneTweet(unittest.TestCase):
    """get_one_tweet() 取得のテスト"""
    def setUp(self):
        self.sys_argv = copy.deepcopy(sys.argv)

    def tearDown(self):
        del sys.argv[:]
        sys.argv = copy.deepcopy(self.sys_argv)

    def test_get_one_tweet_001(self):
        """-i オプションによる get_one_tweet() テスト"""
        config = set_sys_args('-i', '1268346734951964672', '-o', '-')
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

    def test_get_one_tweet_002(self):
        """-i オプションによる generate() テスト(CSV)"""
        outputfilename = tempfile.gettempprefix() + '.csv'
        if os.path.exists(outputfilename):
            os.remove(outputfilename)
        config = set_sys_args('-i', '1268346734951964672', '-o', outputfilename)
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

    def test_get_one_tweet_003(self):
        """-i オプションによる generate() 追記テスト(CSV)"""
        outputfilename = tempfile.gettempprefix() + '.csv'
        if os.path.exists(outputfilename):
            os.remove(outputfilename)
        config = set_sys_args('-i', '1268346734951964672', '-o', outputfilename)
        splunk_writer = twsearch.SplunkWriterBySearch(config)
        splunk_writer.generate(config)
        splunk_writer.flush()
        del splunk_writer
        config = set_sys_args('-i', '1268346734951964672', '-o', outputfilename)
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

    def test_get_one_tweet_004(self):
        """-i オプションによる generate() テスト(CSV ヘッダ付き)"""
        outputfilename = tempfile.gettempprefix() + '.csv'
        if os.path.exists(outputfilename):
            os.remove(outputfilename)
        config = set_sys_args('-i', '1268346734951964672', '-w', '-o', outputfilename)
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

    def test_get_one_tweet_005(self):
        """-i オプションによる generate() テスト(JSON)"""
        outputfilename = tempfile.gettempprefix() + '.json'
        if os.path.exists(outputfilename):
            os.remove(outputfilename)
        config = set_sys_args('-i', '1268346734951964672', '-j', '-o', outputfilename)
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
